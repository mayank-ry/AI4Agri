"""
AI4Agri Disease Pipeline
Combines CNN (.h5) + HuggingFace ViT for robust disease detection.
Strategy:
  1. CNN runs first (fast, existing model)
  2. If CNN confidence < threshold OR CNN fails → ViT backup runs
  3. If both models agree → confidence boosted
  4. Result includes model_source tag for transparency (Explainable AI)
"""
import numpy as np
import structlog
from PIL import Image
import io
from typing import Optional

log = structlog.get_logger()

# Confidence threshold: if CNN is below this, also run ViT
CNN_CONFIDENCE_THRESHOLD = 0.70
# If both models agree, boost confidence by this factor
AGREEMENT_BOOST = 0.05

# ── CNN Disease Classes (matches your MobileNetV2 training) ──────────
# Update this list to match your actual model's class names
CNN_CLASSES = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust",
    "Apple___healthy", "Blueberry___healthy", "Cherry___Powdery_mildew",
    "Cherry___healthy", "Corn___Cercospora_leaf_spot",
    "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy",
    "Grape___Black_rot", "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot",
    "Peach___healthy", "Pepper___Bacterial_spot", "Pepper___healthy",
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
    "Raspberry___healthy", "Rice___Blast", "Rice___Blight",
    "Soybean___healthy", "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch", "Strawberry___healthy",
    "Sugarcane___Red_rot", "Tomato___Bacterial_spot",
    "Tomato___Early_blight", "Tomato___Late_blight",
    "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites", "Tomato___Target_Spot",
    "Tomato___Mosaic_virus", "Tomato___healthy",
    "Wheat___Brown_rust", "Wheat___Healthy", "Wheat___Yellow_rust",
]

# Expanded treatment database
TREATMENT_DB = {
    "Tomato Early Blight": {
        "treatment_en": "Apply chlorothalonil fungicide. Remove affected leaves. Ensure proper spacing for air circulation.",
        "treatment_hi": "क्लोरोथैलोनिल फफूंदनाशक लगाएं। प्रभावित पत्तियां हटाएं। हवा के लिए उचित दूरी रखें।",
        "estimated_cost": "₹200-400",
        "severity_default": "moderate",
    },
    "Tomato Late Blight": {
        "treatment_en": "Use copper-based fungicide immediately. Avoid overhead irrigation. Destroy infected plants.",
        "treatment_hi": "तुरंत तांबा-आधारित फफूंदनाशक लगाएं। ऊपर से सिंचाई बंद करें। संक्रमित पौधे नष्ट करें।",
        "estimated_cost": "₹300-500",
        "severity_default": "severe",
    },
    "Tomato Bacterial Spot": {
        "treatment_en": "Apply copper hydroxide spray. Remove infected leaves. Avoid working in wet fields.",
        "treatment_hi": "कॉपर हाइड्रॉक्साइड स्प्रे करें। संक्रमित पत्तियां हटाएं। गीले खेत में काम से बचें।",
        "estimated_cost": "₹250-400",
        "severity_default": "moderate",
    },
    "Tomato Leaf Mold": {
        "treatment_en": "Improve ventilation. Apply mancozeb fungicide. Reduce humidity around plants.",
        "treatment_hi": "हवा का प्रवाह बढ़ाएं। मैंकोजेब फफूंदनाशक लगाएं। पौधों के आसपास नमी कम करें।",
        "estimated_cost": "₹200-350",
        "severity_default": "mild",
    },
    "Tomato Septoria Leaf Spot": {
        "treatment_en": "Remove infected leaves. Apply chlorothalonil. Mulch around base of plants.",
        "treatment_hi": "संक्रमित पत्तियां हटाएं। क्लोरोथैलोनिल लगाएं। पौधों की जड़ों के आसपास मल्च करें।",
        "estimated_cost": "₹200-300",
        "severity_default": "moderate",
    },
    "Tomato Mosaic Virus": {
        "treatment_en": "No cure exists. Remove infected plants. Disinfect tools. Plant resistant varieties.",
        "treatment_hi": "कोई इलाज नहीं है। संक्रमित पौधे हटाएं। औजारों को कीटाणुरहित करें। प्रतिरोधी किस्में लगाएं।",
        "estimated_cost": "₹100-200",
        "severity_default": "severe",
    },
    "Wheat Brown Rust": {
        "treatment_en": "Apply propiconazole or tebuconazole fungicide. Spray early morning for best results.",
        "treatment_hi": "प्रोपिकोनाज़ोल या टेबुकोनाज़ोल फफूंदनाशक लगाएं। सुबह जल्दी स्प्रे करें।",
        "estimated_cost": "₹400-600",
        "severity_default": "moderate",
    },
    "Wheat Yellow Rust": {
        "treatment_en": "Spray triadimefon immediately. Monitor field daily. Use resistant seed varieties.",
        "treatment_hi": "तुरंत ट्रायडिमेफॉन स्प्रे करें। रोज़ खेत की निगरानी करें। प्रतिरोधी बीज इस्तेमाल करें।",
        "estimated_cost": "₹400-700",
        "severity_default": "severe",
    },
    "Rice Blast": {
        "treatment_en": "Apply tricyclazole or carbendazim. Maintain proper water level in field. Avoid excess nitrogen.",
        "treatment_hi": "ट्राईसाइक्लाज़ोल या कार्बेन्डाज़िम लगाएं। खेत में पानी का स्तर ठीक रखें। ज़्यादा नाइट्रोजन से बचें।",
        "estimated_cost": "₹350-550",
        "severity_default": "severe",
    },
    "Rice Blight": {
        "treatment_en": "Drain excess water. Apply streptocycline 0.01%. Use balanced fertilizer.",
        "treatment_hi": "अतिरिक्त पानी निकालें। स्ट्रेप्टोसाइक्लीन 0.01% लगाएं। संतुलित उर्वरक का उपयोग करें।",
        "estimated_cost": "₹300-500",
        "severity_default": "moderate",
    },
    "Potato Early Blight": {
        "treatment_en": "Apply mancozeb or chlorothalonil spray. Remove infected foliage. Maintain irrigation schedule.",
        "treatment_hi": "मैंकोजेब या क्लोरोथैलोनिल स्प्रे करें। संक्रमित पत्तियां हटाएं। सिंचाई समय पर करें।",
        "estimated_cost": "₹250-400",
        "severity_default": "moderate",
    },
    "Potato Late Blight": {
        "treatment_en": "Use metalaxyl + mancozeb combination. Destroy infected tubers. Hill soil around stems.",
        "treatment_hi": "मेटालैक्सिल + मैंकोजेब मिश्रण लगाएं। संक्रमित कंद नष्ट करें। तनों के आसपास मिट्टी चढ़ाएं।",
        "estimated_cost": "₹400-600",
        "severity_default": "severe",
    },
    "Corn Common Rust": {
        "treatment_en": "Apply propiconazole fungicide. Plant resistant hybrids. Monitor humidity levels.",
        "treatment_hi": "प्रोपिकोनाज़ोल फफूंदनाशक लगाएं। प्रतिरोधी किस्में लगाएं। नमी के स्तर की निगरानी करें।",
        "estimated_cost": "₹300-500",
        "severity_default": "moderate",
    },
    "Corn Northern Leaf Blight": {
        "treatment_en": "Apply azoxystrobin fungicide. Rotate crops. Remove crop residue after harvest.",
        "treatment_hi": "एज़ॉक्सीस्ट्रोबिन फफूंदनाशक लगाएं। फसल चक्र अपनाएं। कटाई के बाद अवशेष हटाएं।",
        "estimated_cost": "₹350-550",
        "severity_default": "moderate",
    },
    "Sugarcane Red Rot": {
        "treatment_en": "Remove infected canes. Treat setts with carbendazim before planting. Use resistant varieties.",
        "treatment_hi": "संक्रमित गन्ने हटाएं। बुआई से पहले कार्बेन्डाज़िम से उपचारित करें। प्रतिरोधी किस्में लगाएं।",
        "estimated_cost": "₹300-500",
        "severity_default": "severe",
    },
    "Grape Black Rot": {
        "treatment_en": "Apply myclobutanil fungicide. Remove mummified berries. Improve air circulation.",
        "treatment_hi": "माइक्लोब्यूटानिल फफूंदनाशक लगाएं। सूखे अंगूर हटाएं। हवा का प्रवाह बढ़ाएं।",
        "estimated_cost": "₹400-600",
        "severity_default": "moderate",
    },
    "Pepper Bacterial Spot": {
        "treatment_en": "Apply copper-based bactericide. Avoid overhead watering. Remove affected leaves.",
        "treatment_hi": "तांबा-आधारित जीवाणुनाशक लगाएं। ऊपर से पानी देने से बचें। प्रभावित पत्तियां हटाएं।",
        "estimated_cost": "₹250-400",
        "severity_default": "moderate",
    },
    "Apple Apple Scab": {
        "treatment_en": "Apply captan or myclobutanil in spring. Rake and destroy fallen leaves. Prune for airflow.",
        "treatment_hi": "वसंत में कैप्टान या माइक्लोब्यूटानिल लगाएं। गिरी पत्तियां हटाएं। हवा के लिए छंटाई करें।",
        "estimated_cost": "₹400-600",
        "severity_default": "moderate",
    },
    "Apple Black Rot": {
        "treatment_en": "Prune dead branches. Apply captan fungicide. Remove mummified fruit from tree.",
        "treatment_hi": "सूखी शाखाएं काटें। कैप्टान फफूंदनाशक लगाएं। पेड़ से सूखे फल हटाएं।",
        "estimated_cost": "₹350-500",
        "severity_default": "moderate",
    },
    "Healthy": {
        "treatment_en": "Crop looks healthy! Continue current farming practices. Monitor regularly.",
        "treatment_hi": "फसल स्वस्थ दिख रही है! वर्तमान खेती के तरीके जारी रखें। नियमित निगरानी करें।",
        "estimated_cost": "₹0",
        "severity_default": "none",
    },
    "Unknown Disease": {
        "treatment_en": "Consult local agricultural expert. Apply broad-spectrum fungicide as precaution.",
        "treatment_hi": "स्थानीय कृषि विशेषज्ञ से संपर्क करें। सावधानी के तौर पर ब्रॉड-स्पेक्ट्रम फफूंदनाशक लगाएं।",
        "estimated_cost": "₹200-500",
        "severity_default": "moderate",
    },
}


def _clean_class_name(raw: str) -> str:
    """Convert CNN class name like 'Tomato___Early_blight' to 'Tomato Early Blight'."""
    return raw.replace("___", " ").replace("_", " ").title()


def _preprocess_for_cnn(image_bytes: bytes, target_size=(224, 224)) -> np.ndarray:
    """Resize and normalize image for MobileNetV2 CNN inference."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(target_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)


def predict_cnn(image_bytes: bytes) -> Optional[dict]:
    """Run prediction on existing CNN .h5 model."""
    from ml.model_manager import get_model
    cnn = get_model("disease_cnn")
    if cnn is None:
        return None
    try:
        batch = _preprocess_for_cnn(image_bytes)
        preds = cnn.predict(batch, verbose=0)[0]
        top_idx = int(np.argmax(preds))
        confidence = float(preds[top_idx])
        # Top-3
        top3_idx = np.argsort(preds)[-3:][::-1]
        top3 = [{"label": _clean_class_name(CNN_CLASSES[i]), "score": round(float(preds[i]), 4)} for i in top3_idx if i < len(CNN_CLASSES)]
        disease_raw = CNN_CLASSES[top_idx] if top_idx < len(CNN_CLASSES) else "Unknown"
        return {
            "disease_name": _clean_class_name(disease_raw),
            "confidence": round(confidence, 4),
            "top3": top3,
            "model_source": "cnn_mobilenetv2",
        }
    except Exception as e:
        log.error("cnn_predict_failed", error=str(e))
        return None


def predict_vit(image_bytes: bytes) -> Optional[dict]:
    """Run prediction on HuggingFace ViT backup model."""
    from ml.model_manager import get_model
    vit = get_model("vit_detector")
    if vit is None:
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = vit(img)
        top = results[0]
        return {
            "disease_name": top["label"].replace("_", " ").title(),
            "confidence": round(float(top["score"]), 4),
            "top3": [{"label": r["label"].replace("_", " ").title(), "score": round(float(r["score"]), 4)} for r in results[:3]],
            "model_source": "hf_vit_backup",
        }
    except Exception as e:
        log.error("vit_predict_failed", error=str(e))
        return None


def run_disease_pipeline(image_bytes: bytes) -> dict:
    """
    Combined CNN + ViT disease detection pipeline.
    Returns a single unified result with model_source transparency.
    """
    # Step 1: Try CNN first (fast, existing model)
    cnn_result = predict_cnn(image_bytes)

    # Step 2: Decide if ViT backup is needed
    need_vit = (cnn_result is None) or (cnn_result["confidence"] < CNN_CONFIDENCE_THRESHOLD)
    vit_result = predict_vit(image_bytes) if need_vit else None

    # Step 3: Combine / select best result
    if cnn_result and vit_result:
        # Both ran — pick higher confidence, but check agreement
        cnn_name = cnn_result["disease_name"].lower().split()[0]
        vit_name = vit_result["disease_name"].lower().split()[0]
        models_agree = cnn_name == vit_name

        if vit_result["confidence"] > cnn_result["confidence"]:
            final = vit_result.copy()
        else:
            final = cnn_result.copy()

        if models_agree:
            final["confidence"] = min(1.0, final["confidence"] + AGREEMENT_BOOST)
            final["model_source"] = "ensemble_agree"
        else:
            final["model_source"] = "ensemble_disagree"

        final["cnn_result"] = {"disease": cnn_result["disease_name"], "confidence": cnn_result["confidence"]}
        final["vit_result"] = {"disease": vit_result["disease_name"], "confidence": vit_result["confidence"]}

    elif cnn_result:
        final = cnn_result.copy()
    elif vit_result:
        final = vit_result.copy()
    else:
        final = {
            "disease_name": "Unknown Disease",
            "confidence": 0.0,
            "top3": [],
            "model_source": "all_models_failed",
        }

    # Step 4: Attach treatment info
    disease = final["disease_name"]
    treatment = TREATMENT_DB.get(disease, TREATMENT_DB["Unknown Disease"])
    final["treatment_en"] = treatment["treatment_en"]
    final["treatment_hi"] = treatment["treatment_hi"]
    final["estimated_cost"] = treatment["estimated_cost"]

    # Step 5: Determine severity
    conf = final["confidence"]
    if disease.lower().endswith("healthy") or disease == "Healthy":
        final["severity"] = "none"
    elif conf > 0.85:
        final["severity"] = "severe"
    elif conf > 0.60:
        final["severity"] = "moderate"
    else:
        final["severity"] = "mild"

    return final
