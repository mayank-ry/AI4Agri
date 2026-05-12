## backend/ml/prompt_templates.py
"""
Utility functions that build prompt strings for the AI models.
All prompts are crafted to produce **Hindi** answers (or bilingual where required).
"""

from typing import Dict


def chat_system_prompt(field: Dict, health: Dict, farmer: Dict) -> str:
    """Build the system prompt for the main chatbot.
    The prompt gives the model a concise context and forces Hindi output.
    """
    crop = field.get("crop_type", "अज्ञात फसल")
    stage = field.get("growth_stage", "विकास चरण")
    ndvi = health.get("ndvi_score", "N/A")
    ws = health.get("wsri_score", "N/A")
    disease = health.get("latest_disease", "कोई नहीं")
    location = f"{farmer.get('district','')}, {farmer.get('state','')}".strip(", ")
    return (
        "आप किसान मित्र, एक अनुभवी भारतीय कृषि विशेषज्ञ हैं। "
        "सभी उत्तर हिंदी में, संक्षिप्त (अधिकतम 4 वाक्य) दें।\n"
        f"फसल: {crop}, चरण: {stage}\n"
        f"NDVI: {ndvi}, जल तनाव: {ws}%\n"
        f"हालिया रोग: {disease}\n"
        f"स्थान: {location}\n"
        "नियम:\n"
        "- प्रश्न में मौजूद भाषा के अनुसार उत्तर दें (हिंदी → हिंदी, अंग्रेजी → अंग्रेजी)।\n"
        "- हमेशा फसल का नाम स्पष्ट रूप से बताएं।\n"
        "- व्यावहारिक, कार्रवाई योग्य सलाह प्रदान करें।"
    )


def advisory_prompt(context: Dict) -> str:
    """Build a Flan‑T5 prompt that explicitly asks for Hindi output.
    Expected keys in *context*: crop, stage, issue, weather, ndvi, ws, disease.
    """
    crop = context.get("crop", "फसल")
    stage = context.get("stage", "विकास चरण")
    issue = context.get("issue", "कोई समस्या नहीं")
    weather = context.get("weather", "मौसम डेटा उपलब्ध नहीं")
    ndvi = context.get("ndvi", "N/A")
    ws = context.get("ws", "N/A")
    disease = context.get("disease", "कोई नहीं")
    return (
        f"किसान ने {crop} की {stage} अवस्था में समस्या बताई है: {issue}. "
        f"NDVI: {ndvi}, जल तनाव: {ws}%, रोग: {disease}. "
        f"मौसम/पर्यावरणीय स्थिति: {weather}. "
        "सिर्फ दो व्यावहारिक, सरल, हिंदी में फसल प्रबंधन की सलाह दें।"
    )
