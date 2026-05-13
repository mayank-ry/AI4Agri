"""Inference service wrappers around the local model registry."""

import structlog

from ml.model_manager import get_model

log = structlog.get_logger()

KEYWORD_INTENTS = {
    "jal": "urgent_distress", "mar": "urgent_distress", "sukh": "urgent_distress",
    "kharab": "urgent_distress", "mur": "urgent_distress", "girr": "urgent_distress",
    "barbaad": "urgent_distress", "nast": "urgent_distress", "bimar": "urgent_distress",
    "rog": "urgent_distress", "kida": "urgent_distress", "keeda": "urgent_distress",
    "pila": "urgent_distress", "safed": "urgent_distress", "dhabbe": "urgent_distress",
    "mausam": "weather_query", "barish": "weather_query", "baarish": "weather_query",
    "garmi": "weather_query", "thandi": "weather_query", "thand": "weather_query",
    "paani": "irrigation_query", "pani": "irrigation_query", "sinchai": "irrigation_query",
    "water": "irrigation_query", "nami": "irrigation_query", "sukha": "irrigation_query",
    "khad": "fertilizer_query", "urea": "fertilizer_query", "dap": "fertilizer_query",
    "fertilizer": "fertilizer_query", "nitrogen": "fertilizer_query",
    "paidawar": "yield_query", "upaj": "yield_query", "mandi": "market_query",
    "bhav": "market_query", "rate": "market_query",
}


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
        max_length: int = 150,
    ) -> str:
        model = self._ensure_loaded()
        if not model:
            return "Kheti ki salah abhi uplabdh nahi hai. Kripya baad mein prayas karein."

        prompt = f"""Provide practical farming advice in {lang}:
Crop: {crop}
Growth Stage: {stage}
Problem: {issue}
Weather: {weather}

Advice:"""

        try:
            result = model(prompt, max_length=max_length, do_sample=False)
            if result:
                return result[0]["generated_text"].strip()
        except Exception as e:
            log.error("flan_t5_generation_failed", error=str(e))

        return "Kripya baad mein prayas karein."


class IntentClassificationService:
    """Keyword-first intent classifier with local model urgency fallback."""

    def __init__(self):
        self.model = None

    def _ensure_loaded(self):
        if self.model is None:
            self.model = get_model("intent")
        return self.model

    @staticmethod
    def _keyword_intent(text: str) -> str:
        text_lower = text.lower()
        for keyword, intent in KEYWORD_INTENTS.items():
            if keyword in text_lower:
                return intent
        return "general_query"

    def classify(self, text: str) -> dict:
        keyword_intent = self._keyword_intent(text)
        priority = "HIGH" if keyword_intent == "urgent_distress" else "NORMAL"
        priority_hi = "Zaruri hai! Turant madad chahiye." if priority == "HIGH" else "Samanya"
        urgency_score = 0.85 if priority == "HIGH" else 0.5

        model = self._ensure_loaded()
        if model:
            try:
                result = model(text, truncation=True, max_length=512)
                if result:
                    label = result[0]["label"]
                    score = float(result[0]["score"])
                    urgency_score = score
                    if keyword_intent == "urgent_distress" or label in {"NEGATIVE", "LABEL_0"}:
                        priority = "HIGH"
                        priority_hi = "Zaruri hai! Turant madad chahiye."
                    elif label in {"POSITIVE", "LABEL_2"}:
                        priority = "LOW"
                        priority_hi = "Kam"
            except Exception as e:
                log.error("intent_classification_failed", error=str(e))

        return {
            "intent": keyword_intent,
            "urgency_score": urgency_score,
            "priority": priority,
            "priority_hi": priority_hi,
        }


_flan_t5_service = FlanT5InferenceService()
_intent_service = IntentClassificationService()


def get_flan_t5_service() -> FlanT5InferenceService:
    return _flan_t5_service


def get_intent_service() -> IntentClassificationService:
    return _intent_service
