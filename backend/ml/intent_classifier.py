"""
AI4Agri Intent Classifier
Uses cardiffnlp/twitter-roberta-base-sentiment to detect user intent/urgency.
Maps raw sentiment labels to farming-specific intents for the chatbot.
"""
import structlog
from typing import Optional

log = structlog.get_logger()

# ── Intent Mapping ──────────────────────────────────────────────────
# RoBERTa outputs: LABEL_0 (negative), LABEL_1 (neutral), LABEL_2 (positive)
# We map these + keyword rules to farming intents.

KEYWORD_INTENTS = {
    # Urgent / Distress
    "jal": "urgent_distress", "mar": "urgent_distress", "sukh": "urgent_distress",
    "kharab": "urgent_distress", "mur": "urgent_distress", "girr": "urgent_distress",
    "barbaad": "urgent_distress", "nast": "urgent_distress", "bimar": "urgent_distress",
    "rog": "urgent_distress", "kida": "urgent_distress", "keeda": "urgent_distress",
    "pila": "urgent_distress", "safed": "urgent_distress", "dhabbe": "urgent_distress",
    "toot": "urgent_distress", "tut": "urgent_distress",
    # Weather
    "mausam": "weather_query", "barish": "weather_query", "baarish": "weather_query",
    "garmi": "weather_query", "thandi": "weather_query", "thand": "weather_query",
    "loo": "weather_query", "aandhi": "weather_query", "toofan": "weather_query",
    # Irrigation
    "paani": "irrigation_query", "pani": "irrigation_query", "sinchai": "irrigation_query",
    "water": "irrigation_query", "nami": "irrigation_query", "sukha": "irrigation_query",
    # Fertilizer
    "khad": "fertilizer_query", "urea": "fertilizer_query", "dap": "fertilizer_query",
    "fertilizer": "fertilizer_query", "nitrogen": "fertilizer_query",
    # Harvest / Yield
    "fasal": "crop_query", "paidawar": "yield_query", "munafa": "yield_query",
    "upaj": "yield_query", "bechna": "market_query", "mandi": "market_query",
    "bhav": "market_query", "rate": "market_query",
}


def classify_intent(message: str) -> dict:
    """
    Classify farmer's chatbot message into intent + urgency.
    Uses keyword matching first (fast, accurate for Hindi/Hinglish),
    then falls back to RoBERTa sentiment for urgency scoring.
    """
    msg_lower = message.lower()

    # ── Step 1: Keyword-based intent detection ──────────────────────
    detected_intent = "general_query"
    for keyword, intent in KEYWORD_INTENTS.items():
        if keyword in msg_lower:
            detected_intent = intent
            break

    # ── Step 2: Sentiment/urgency via RoBERTa ───────────────────────
    urgency_score = 0.5  # neutral default
    sentiment_label = "neutral"
    try:
        from ml.model_manager import get_model
        classifier = get_model("intent")
        if classifier:
            result = classifier(message[:512])[0]
            label = result["label"]   # LABEL_0, LABEL_1, LABEL_2
            score = result["score"]

            if label == "LABEL_0":     # negative
                sentiment_label = "negative"
                urgency_score = 0.6 + 0.4 * score
            elif label == "LABEL_2":   # positive
                sentiment_label = "positive"
                urgency_score = max(0.1, 0.5 - 0.4 * score)
            else:                      # neutral
                sentiment_label = "neutral"
                urgency_score = 0.5
    except Exception as e:
        log.warning("intent_classifier_fallback", error=str(e))

    # ── Step 3: Override urgency if keywords scream distress ────────
    if detected_intent == "urgent_distress":
        urgency_score = max(urgency_score, 0.85)

    # ── Priority label ──────────────────────────────────────────────
    if urgency_score >= 0.8:
        priority = "HIGH"
        priority_hi = "Zaruri hai! Turant madad chahiye."
    elif urgency_score >= 0.5:
        priority = "MEDIUM"
        priority_hi = "Dhyan dena zaruri hai."
    else:
        priority = "LOW"
        priority_hi = "Sab theek lag raha hai."

    return {
        "intent": detected_intent,
        "sentiment": sentiment_label,
        "urgency_score": round(urgency_score, 3),
        "priority": priority,
        "priority_hi": priority_hi,
    }
