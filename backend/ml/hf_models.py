"""
AI4Agri HuggingFace Models - Simplified API layer
Now delegates to model_manager.py for all loading.
Direct model access via model_manager.get_model().
This file provides high-level utility functions used by routes.
"""
import structlog
import os
from typing import Optional

log = structlog.get_logger()

HF_CACHE = os.getenv("HF_CACHE_DIR", "backend/ml/hf_cache")
os.makedirs(HF_CACHE, exist_ok=True)


def translate_to_hindi(text: str) -> str:
    """Translate English text to Hindi. Chunks long text. Falls back to original."""
    if not text or not text.strip():
        return text
    try:
        from ml.model_manager import get_model
        translator = get_model("translator")
        if translator is None:
            return text

        MAX_CHUNK = 400
        if len(text) <= MAX_CHUNK:
            result = translator(text)
            return result[0]["translation_text"]
        else:
            chunks = [text[i:i+MAX_CHUNK] for i in range(0, len(text), MAX_CHUNK)]
            parts = []
            for chunk in chunks:
                r = translator(chunk)
                parts.append(r[0]["translation_text"])
            return " ".join(parts)
    except Exception as e:
        log.error("translate_to_hindi_failed", error=str(e))
        return text  # Safe fallback


def generate_advice(crop: str, stage: str, issue: str, weather: str, lang: str = "en") -> str:
    """Generate farming advice using Flan‑T5. If `lang` is "hi" the output is translated to Hindi.
    Falls back to a static message if the model cannot be loaded.
    """
    prompt = (
        f"Farmer has {crop} crop at {stage} stage. "
        f"Issue: {issue}. Weather: {weather}. "
        f"Give 2 specific actionable farming tips in simple language."
    )
    try:
        from ml.model_manager import get_model
        advisor = get_model("advisor")
        if advisor is None:
            base_msg = f"{crop} fasal ki dhyan se dekh‑rekh karein aur nazdiki krishi kendra se salah lein."
            return base_msg if lang == "hi" else base_msg
        result = advisor(prompt, max_length=120, do_sample=False)[0]
        advice = result["generated_text"].strip()
        if lang == "hi":
            # Translate using the singleton TranslatorService
            from ml.translator_service import TranslatorService
            advice = TranslatorService().translate(advice)
        return advice
    except Exception as e:
        log.error("generate_advice_failed", error=str(e))
        fallback = f"{crop} fasal ki dhyan se dekh‑rekh karein aur nazdiki krishi kendra se salah lein."
        return fallback if lang == "hi" else fallback
    """Generate farming advice using Flan-T5. Falls back to static message."""
    prompt = (
        f"Farmer has {crop} crop at {stage} stage. "
        f"Issue: {issue}. Weather: {weather}. "
        f"Give 2 specific actionable farming tips in simple language."
    )
    try:
        from ml.model_manager import get_model
        advisor = get_model("advisor")
        if advisor is None:
            return f"{crop} fasal ki dhyan se dekh-rekh karein aur nazdiki krishi kendra se salah lein."
        result = advisor(prompt, max_length=120, do_sample=False)[0]
        return result["generated_text"]
    except Exception as e:
        log.error("generate_advice_failed", error=str(e))
        return f"{crop} fasal ki dhyan se dekh-rekh karein aur nazdiki krishi kendra se salah lein."


def backup_disease_detect(image_bytes: bytes) -> dict:
    """
    DEPRECATED: Use ml.disease_pipeline.run_disease_pipeline() instead.
    Kept for backward compatibility with existing route imports.
    """
    from ml.disease_pipeline import predict_vit
    result = predict_vit(image_bytes)
    if result:
        return {
            "disease_name": result["disease_name"],
            "confidence": result["confidence"],
            "top3": result["top3"],
            "model_used": "hf_vit_backup",
        }
    return {
        "disease_name": "Unknown Disease",
        "confidence": 0.0,
        "top3": [],
        "model_used": "hf_backup_failed",
    }
