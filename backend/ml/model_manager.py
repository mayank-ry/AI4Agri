"""
AI4Agri Model Manager
Centralized loading, caching, and lifecycle management for all ML models.
Strategy: Use ONLY local cached models, no HuggingFace downloads.
Lazy loading with CPU-only inference for Windows + Python 3.11.
"""
import os
import time
import structlog
from enum import Enum
from typing import Optional, Any
from pathlib import Path

log = structlog.get_logger()

# Force CPU-only for HuggingFace models
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Local cache directory with pre-downloaded models
import os
from pathlib import Path

# Find cache relative to this file's location
_current_dir = Path(__file__).parent
LOCAL_CACHE = str(_current_dir / "cache")

if not os.path.exists(LOCAL_CACHE):
    raise FileNotFoundError(f"Model cache not found at {LOCAL_CACHE}. Please download models first.")

log.info("using_local_model_cache", path=LOCAL_CACHE)


class ModelStatus(str, Enum):
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"


class ManagedModel:
    """Wrapper around a single model with status tracking and load timing."""
    def __init__(self, name: str, load_fn, preload: bool = False):
        self.name = name
        self._load_fn = load_fn
        self.preload = preload
        self.status = ModelStatus.NOT_LOADED
        self.instance: Any = None
        self.load_time_ms: float = 0
        self.error: Optional[str] = None

    def load(self):
        if self.status == ModelStatus.READY:
            return self.instance
        self.status = ModelStatus.LOADING
        start = time.time()
        try:
            self.instance = self._load_fn()
            self.load_time_ms = round((time.time() - start) * 1000, 1)
            self.status = ModelStatus.READY
            log.info("model_loaded", model=self.name, time_ms=self.load_time_ms)
            return self.instance
        except Exception as e:
            self.status = ModelStatus.FAILED
            self.error = str(e)
            log.error("model_load_failed", model=self.name, error=str(e))
            return None

    def get(self):
        """Lazy-load and return the model instance."""
        if self.status == ModelStatus.READY:
            return self.instance
        return self.load()

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status.value,
            "load_time_ms": self.load_time_ms,
            "preload": self.preload,
            "error": self.error,
        }


# ── Model Loader Functions (LOCAL ONLY) ─────────────────────────────

def _load_disease_cnn():
    """Load MobileNetV2 CNN model from local cache."""
    model_path = os.getenv("DISEASE_MODEL_PATH", "backend/ml/models/plant_disease_mobilenetv2.h5")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"CNN model not found at {model_path}")
    import tensorflow as tf
    model = tf.keras.models.load_model(model_path, compile=False)
    log.info("cnn_disease_model_loaded", path=model_path)
    return model


def _load_vit_detector():
    """Load ViT model from local cache."""
    from transformers import pipeline
    cache_path = os.path.join(LOCAL_CACHE, "vit")
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"ViT model cache not found at {cache_path}")
    
    return pipeline(
        "image-classification",
        model=cache_path,
        device=-1,  # Force CPU
    )


def _load_flan_t5():
    """Load Flan-T5 text generation model from local cache."""
    from transformers import pipeline
    cache_path = os.path.join(LOCAL_CACHE, "flan")
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Flan-T5 model cache not found at {cache_path}")
    
    return pipeline(
        "text2text-generation",
        model=cache_path,
        device=-1,
        max_length=200,
    )


def _load_intent_classifier():
    """Load intent/sentiment classifier from local cache."""
    from transformers import pipeline
    cache_path = os.path.join(LOCAL_CACHE, "intent")
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Intent classifier cache not found at {cache_path}")
    
    return pipeline(
        "sentiment-analysis",
        model=cache_path,
        device=-1,
    )


def _load_translator():
    """Load translation model from local cache."""
    from transformers import pipeline
    cache_path = os.path.join(LOCAL_CACHE, "translation")
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Translation model cache not found at {cache_path}")
    
    return pipeline(
        "translation",
        model=cache_path,
        device=-1,
    )


# ── Global Registry ────────────────────────────────────────────────

_registry: dict[str, ManagedModel] = {
    # PRELOAD at startup (critical for chatbot)
    "flan_t5":        ManagedModel("flan_t5",        _load_flan_t5,           preload=True),
    "intent":         ManagedModel("intent",         _load_intent_classifier, preload=True),
    
    # LAZY LOAD (loaded on first request to save RAM)
    "disease_cnn":    ManagedModel("disease_cnn",    _load_disease_cnn,       preload=False),
    "vit_detector":   ManagedModel("vit_detector",   _load_vit_detector,      preload=False),
    "translator":     ManagedModel("translator",     _load_translator,        preload=False),
}


def get_model(name: str) -> Any:
    """Get a model by name. Lazy-loads if not yet loaded."""
    if name not in _registry:
        raise KeyError(f"Unknown model: {name}. Available: {list(_registry.keys())}")
    return _registry[name].get()


def preload_all():
    """Called once at FastAPI startup. Loads models marked preload=True."""
    log.info("preloading_models_start")
    for name, mm in _registry.items():
        if mm.preload:
            mm.load()
    log.info("preloading_models_done")


def get_all_status() -> list[dict]:
    """Returns status of every registered model (for /health endpoint)."""
    return [mm.to_dict() for mm in _registry.values()]
