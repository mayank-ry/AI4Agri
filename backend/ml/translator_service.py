import os
import structlog
from transformers import pipeline
from typing import List

log = structlog.get_logger()

class TranslatorService:
    """Singleton service that loads a HuggingFace translation pipeline.
    Provides single string and batch translation with simple chunking.
    """
    _instance = None
    _pipeline = None
    _cache_dir: str = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslatorService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pipeline is None:
            self._cache_dir = os.getenv("HF_CACHE_DIR", "backend/ml/hf_cache")
            os.makedirs(self._cache_dir, exist_ok=True)
            try:
                log.info("Loading Hindi translation model (Helsinki-NLP/opus-mt-en-hi)")
                self._pipeline = pipeline(
                    "translation_en_to_hi",
                    model="Helsinki-NLP/opus-mt-en-hi",
                    cache_dir=self._cache_dir,
                )
            except Exception as e:
                log.error("translation_model_load_failed", error=str(e))
                self._pipeline = None

    def translate(self, text: str) -> str:
        """Translate a single English string to Hindi.
        Returns original text on any failure.
        """
        if not text or self._pipeline is None:
            return text
        try:
            result = self._pipeline(text)
            return result[0]["translation_text"] if result else text
        except Exception as e:
            log.error("translation_failed", error=str(e))
            return text

    def batch_translate(self, texts: List[str]) -> List[str]:
        """Translate a list of strings.
        The HuggingFace pipeline has a max token limit (~400 chars).
        We split long strings internally and join them.
        """
        if not texts or self._pipeline is None:
            return texts
        translated: List[str] = []
        for txt in texts:
            if not txt:
                translated.append(txt)
                continue
            # Simple chunking for >400 chars
            if len(txt) > 400:
                chunks = [txt[i:i+400] for i in range(0, len(txt), 400)]
                pieces = []
                for ch in chunks:
                    try:
                        res = self._pipeline(ch)
                        pieces.append(res[0]["translation_text"])
                    except Exception as e:
                        log.error("batch_translation_chunk_failed", error=str(e))
                        pieces.append(ch)
                translated.append(" ".join(pieces))
            else:
                try:
                    res = self._pipeline(txt)
                    translated.append(res[0]["translation_text"])
                except Exception as e:
                    log.error("batch_translation_failed", error=str(e))
                    translated.append(txt)
        return translated
