"""High-level HuggingFace helpers used by API routes."""

import structlog

log = structlog.get_logger()


def translate_to_hindi(text: str) -> str:
    """Translate English text to Hindi using the managed local translator model."""
    if not text or not text.strip():
        return text

    try:
        from ml.model_manager import get_model

        translator = get_model("translator")
        if translator is None:
            return text

        max_chunk = 400
        chunks = [text] if len(text) <= max_chunk else [
            text[i:i + max_chunk] for i in range(0, len(text), max_chunk)
        ]
        translated = [translator(chunk)[0]["translation_text"] for chunk in chunks]
        return " ".join(translated)
    except Exception as e:
        log.error("translate_to_hindi_failed", error=str(e))
        return text
