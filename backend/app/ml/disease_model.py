import os
import json
import asyncio
import cv2
import numpy as np
import structlog
from typing import Tuple, Dict, Any, Optional, List

logger = structlog.get_logger(__name__)

DEFAULT_INPUT_SIZE = (224, 224)

class DiseaseModelWrapper:
    def __init__(self):
        self.model_path = os.getenv("DISEASE_MODEL_PATH", None)
        self.label_mapping_path = os.getenv("LABEL_MAPPING_PATH", "backend/models/label_mapping.json")
        self.is_tflite = self.model_path and self.model_path.endswith('.tflite')
        self.model = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.label_mapping = {}
        self.input_size = DEFAULT_INPUT_SIZE
        
        self._load_label_mapping()
        self.load_model()

    def _load_label_mapping(self):
        """Dynamically load label mappings from JSON."""
        try:
            if os.path.exists(self.label_mapping_path):
                with open(self.label_mapping_path, 'r') as f:
                    mapping = json.load(f)
                    # Convert string keys to int
                    self.label_mapping = {int(k): v for k, v in mapping.items()}
                logger.info("label_mapping_loaded", keys_count=len(self.label_mapping))
            else:
                logger.warning("label_mapping_not_found", path=self.label_mapping_path)
                self.label_mapping = {0: "Healthy", 1: "Unknown Disease"}
        except Exception as e:
            logger.error("label_mapping_error", error=str(e))
            self.label_mapping = {0: "Healthy", 1: "Unknown Disease"}

    def load_model(self):
        """Graceful model loading. Does not crash if model is missing."""
        if not self.model_path:
            logger.warning("DISEASE_MODEL_PATH not set. Inference pipeline is disabled.")
            return

        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found at {self.model_path}. Inference disabled.")
            return

        try:
            import tensorflow as tf
            
            if self.is_tflite:
                logger.info(f"Loading TFLite model from {self.model_path}")
                self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
                # Dynamically determine input size if possible
                shape = self.input_details[0]['shape']
                if len(shape) == 4:
                    self.input_size = (shape[1], shape[2])
                    
            else:
                logger.info(f"Loading H5/Keras model from {self.model_path}")
                self.model = tf.keras.models.load_model(self.model_path)
                
            logger.info("Disease model loaded successfully.")
        except Exception as e:
            logger.error("model_load_failed", error=str(e))
            self.model = None
            self.interpreter = None

    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Decode and preprocess the image using OpenCV and MobileNetV2 logic."""
        import tensorflow as tf
        
        # Decode byte array to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image file.")
            
        # Convert BGR to RGB (OpenCV uses BGR by default, models usually expect RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Resize to expected model input size
        img_resized = cv2.resize(img_rgb, self.input_size)
        
        # MobileNetV2 Preprocessing: scales pixels between -1 and 1
        img_preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(img_resized)
        
        # Add batch dimension -> (1, 224, 224, 3)
        img_batch = np.expand_dims(img_preprocessed, axis=0)
        return img_batch

    def _run_inference(self, image_batch: np.ndarray) -> List[Tuple[int, float]]:
        """Synchronous inference execution returning Top-K results."""
        if self.is_tflite and self.interpreter:
            self.interpreter.set_tensor(self.input_details[0]['index'], image_batch)
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        elif self.model:
            predictions = self.model.predict(image_batch)[0]
        else:
            raise RuntimeError("Model is not loaded.")
            
        # Extract Top 3 predictions
        top_k_indices = np.argsort(predictions)[-3:][::-1]
        
        results = []
        for idx in top_k_indices:
            results.append((int(idx), float(predictions[idx])))
            
        return results

    def _estimate_severity(self, disease_name: str, confidence: float) -> str:
        """Heuristic severity estimation."""
        if confidence < 0.50:
            return "Unknown"
        if disease_name.lower() == "healthy":
            return "None"
            
        if confidence > 0.90:
            return "High"
        elif confidence > 0.70:
            return "Medium"
        return "Low"

    def _get_recommendation(self, disease_name: str, confidence: float) -> str:
        if confidence < 0.50:
            return "The AI is uncertain. Please take a clearer picture or consult an agronomist manually."
        if disease_name.lower() == "healthy":
            return "Maintain current irrigation and nutrient schedules."
        return f"Consult an agronomist for targeted fungicide/bactericide application for {disease_name}."

    async def predict_async(self, image_bytes: bytes) -> Dict[str, Any]:
        """Async-safe wrapper offloading CPU-bound CV2 and TF operations."""
        if not self.model and not self.interpreter:
            raise RuntimeError("Model unavailable.")
            
        # 1. Preprocess in thread
        processed_image = await asyncio.to_thread(self._preprocess_image, image_bytes)
        
        # 2. Run inference in thread
        top_k_results = await asyncio.to_thread(self._run_inference, processed_image)
        
        # 3. Post-process
        top_class_id, top_confidence = top_k_results[0]
        disease_name = self.label_mapping.get(top_class_id, f"Unknown Class {top_class_id}")
        
        # Low confidence fallback
        if top_confidence < 0.50:
            disease_name = "Unrecognized Pattern"
            
        severity = self._estimate_severity(disease_name, top_confidence)
        
        top_k_formatted = []
        for class_id, conf in top_k_results:
            name = self.label_mapping.get(class_id, f"Unknown Class {class_id}")
            top_k_formatted.append({"disease_name": name, "confidence": conf})
            
        # Construct Explainability Fields
        factors = [
            {
                "name": "Model Confidence",
                "value": f"{top_confidence * 100:.1f}%",
                "impact": "high" if top_confidence > 0.8 else "low",
                "description": "The AI certainty level for this classification."
            }
        ]
        
        if top_confidence >= 0.50:
            reasons = [
                f"The image strongly matches the visual signature of {disease_name}.",
                f"Confidence score of {top_confidence * 100:.1f}% exceeds the classification threshold."
            ]
        else:
            reasons = [
                "The image does not strongly match any known disease signatures.",
                f"Highest confidence was only {top_confidence * 100:.1f}%, which is below the 50% threshold."
            ]
            factors.append({
                "name": "Image Quality / Unrecognized",
                "value": "Flagged",
                "impact": "high",
                "description": "The subject may not be a supported leaf, or the image is too blurry."
            })
        
        return {
            "disease_name": disease_name,
            "confidence": top_confidence,
            "severity_level": severity,
            "recommendation_text": self._get_recommendation(disease_name, top_confidence),
            "explanation": f"Analyzed using MobileNetV2 architecture with PlantVillage weights.",
            "reasons": reasons,
            "factors": factors,
            "top_k_predictions": top_k_formatted
        }

# Global Singleton instance
disease_model_wrapper = DiseaseModelWrapper()
