"""
AI4Agri Inference Services
Wraps local cached models with inference APIs for backend routes.
"""
import structlog
from typing import Optional
from ml.model_manager import get_model

log = structlog.get_logger()


class FlanT5InferenceService:
    """Wrapper around Flan-T5 for crop advice generation."""
    
    def __init__(self):
        self.model = None
    
    def _ensure_loaded(self):
        if self.model is None:
            self.model = get_model("flan_t5")
        return self.model
    
    def generate_advice(
        self,
        crop: str,
        stage: str,
        issue: str,
        weather: str,
        lang: str = "hi",
        max_length: int = 150
    ) -> str:
        """Generate farming advice using Flan-T5."""
        model = self._ensure_loaded()
        if not model:
            return "खेती की जानकारी के लिए कृपया बाद में प्रयास करें।"
        
        # Build prompt for Flan-T5
        prompt = f"""Provide practical farming advice in {lang}:
Crop: {crop}
Growth Stage: {stage}
Problem: {issue}
Weather: {weather}

Advice:"""
        
        try:
            result = model(prompt, max_length=max_length, do_sample=False)
            if result and len(result) > 0:
                return result[0]['generated_text'].strip()
            return "खेती की सलाह उपलब्ध नहीं है।"
        except Exception as e:
            log.error("flan_t5_generation_failed", error=str(e))
            return "कृपया बाद में प्रयास करें।"


class IntentClassificationService:
    """Wrapper around intent classifier for understanding farmer queries."""
    
    def __init__(self):
        self.model = None
    
    def _ensure_loaded(self):
        if self.model is None:
            self.model = get_model("intent")
        return self.model
    
    def classify(self, text: str) -> dict:
        """Classify intent and urgency of a farmer's query."""
        model = self._ensure_loaded()
        if not model:
            return {
                "intent": "general",
                "urgency_score": 0.5,
                "priority": "NORMAL",
                "priority_hi": "सामान्य"
            }
        
        try:
            result = model(text, truncation=True, max_length=512)
            if result and len(result) > 0:
                label = result[0]['label']
                score = result[0]['score']
                
                # Map sentiment to farming intent
                if label == "POSITIVE":
                    intent = "satisfaction"
                    priority = "LOW"
                    priority_hi = "कम"
                elif label == "NEGATIVE":
                    intent = "problem"
                    priority = "HIGH"
                    priority_hi = "उच्च"
                else:
                    intent = "general"
                    priority = "NORMAL"
                    priority_hi = "सामान्य"
                
                return {
                    "intent": intent,
                    "urgency_score": float(score),
                    "priority": priority,
                    "priority_hi": priority_hi,
                }
        except Exception as e:
            log.error("intent_classification_failed", error=str(e))
        
        return {
            "intent": "general",
            "urgency_score": 0.5,
            "priority": "NORMAL",
            "priority_hi": "सामान्य"
        }


class DiseaseCNNInferenceService:
    """Wrapper around CNN model for plant disease detection."""
    
    def __init__(self):
        self.model = None
    
    def _ensure_loaded(self):
        if self.model is None:
            self.model = get_model("disease_cnn")
        return self.model
    
    def detect_disease(self, image_array) -> dict:
        """Detect plant disease from image array."""
        model = self._ensure_loaded()
        if not model:
            return {
                "disease": "unknown",
                "confidence": 0.0,
                "recommendation": "कृपया बाद में प्रयास करें।"
            }
        
        try:
            import numpy as np
            prediction = model.predict(np.expand_dims(image_array, axis=0), verbose=0)
            disease_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][disease_idx])
            
            # Map index to disease name (assuming label mapping exists)
            diseases = [
                "apple_scab", "apple_black_rot", "apple_cedar_rust",
                "tomato_early_blight", "tomato_late_blight", "healthy"
            ]
            disease = diseases[min(disease_idx, len(diseases) - 1)]
            
            return {
                "disease": disease,
                "confidence": confidence,
                "recommendation": f"Disease: {disease} detected with {confidence*100:.1f}% confidence."
            }
        except Exception as e:
            log.error("cnn_inference_failed", error=str(e))
            return {
                "disease": "unknown",
                "confidence": 0.0,
                "recommendation": "रोग का पता नहीं लगाया जा सका।"
            }


# ── Global Service Instances ────────────────────────────────────────

_flan_t5_service = FlanT5InferenceService()
_intent_service = IntentClassificationService()
_disease_service = DiseaseCNNInferenceService()


def get_flan_t5_service() -> FlanT5InferenceService:
    return _flan_t5_service


def get_intent_service() -> IntentClassificationService:
    return _intent_service


def get_disease_service() -> DiseaseCNNInferenceService:
    return _disease_service
