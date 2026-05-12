from transformers import pipeline
import structlog

logger = structlog.get_logger(__name__)

class HFService:
    def __init__(self):
        self.translator = None
        self._init_models()

    def _init_models(self):
        try:
            # Initialize English to Hindi translator
            self.translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-hi")
            logger.info("hf_models_loaded")
        except Exception as e:
            logger.error("hf_models_load_failed", error=str(e))

    def translate_to_hindi(self, text: str) -> str:
        if not self.translator or not text:
            return text + " (Hindi)" # Fallback
            
        try:
            # The pipeline returns a list of dicts, e.g., [{'translation_text': '...'}]
            result = self.translator(text)
            if result and isinstance(result, list) and 'translation_text' in result[0]:
                return result[0]['translation_text']
            return text
        except Exception as e:
            logger.error("translation_error", error=str(e))
            return text + " (Hindi)"

hf_service = HFService()
