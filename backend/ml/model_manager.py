"""
AI4Agri Model Manager
Centralized loading, caching, and lifecycle management for all ML models.
Strategy: Use ONLY local cached models, no HuggingFace downloads.
Lazy loading with CPU-only inference for Windows + Python 3.11.
"""
import os
import time
import structlog
import json
import shutil
import tempfile
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
    configured_path = os.getenv("DISEASE_MODEL_PATH")
    candidates = []
    if configured_path:
        candidates.append(Path(configured_path))
        if not Path(configured_path).is_absolute():
            candidates.append(_current_dir.parent.parent / configured_path)
    candidates.append(_current_dir / "models" / "plant_disease_mobilenetv2.h5")

    model_path = next((path for path in candidates if path.exists()), None)
    if model_path is None:
        tried = ", ".join(str(path) for path in candidates)
        raise FileNotFoundError(f"CNN model not found. Tried: {tried}")
    import tensorflow as tf
    try:
        model = tf.keras.models.load_model(str(model_path), compile=False)
    except Exception as e:
        if "InputLayer" not in str(e) or "batch_shape" not in str(e):
            log.warning("cnn_load_model_failed_reconstructing", error=str(e))
            return _reconstruct_mobilenetv2_cnn(tf, model_path)
        try:
            model = _load_keras_h5_with_inputlayer_compat(tf, model_path)
        except Exception as compat_error:
            log.warning("cnn_h5_compat_load_failed_reconstructing", error=str(compat_error))
            model = _reconstruct_mobilenetv2_cnn(tf, model_path)
    log.info("cnn_disease_model_loaded", path=str(model_path))
    return model


def _load_keras_h5_with_inputlayer_compat(tf, model_path: Path):
    """Load Keras 3-style H5 configs with older tf.keras loaders."""
    import h5py

    def patch_layer_config(node):
        if isinstance(node, dict):
            if node.get("class_name") == "InputLayer":
                config = node.get("config", {})
                if "batch_shape" in config and "batch_input_shape" not in config:
                    config["batch_input_shape"] = config.pop("batch_shape")
                config.pop("optional", None)
            config = node.get("config")
            if isinstance(config, dict):
                config.pop("quantization_config", None)
                dtype = config.get("dtype")
                if isinstance(dtype, dict) and dtype.get("class_name") == "DTypePolicy":
                    config["dtype"] = dtype.get("config", {}).get("name", "float32")
            for value in node.values():
                patch_layer_config(value)
        elif isinstance(node, list):
            for item in node:
                patch_layer_config(item)

    with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        shutil.copy2(model_path, temp_path)
        with h5py.File(temp_path, "r+") as h5_file:
            raw_config = h5_file.attrs.get("model_config")
            if raw_config is None:
                raise ValueError("H5 model_config attribute missing")
            if isinstance(raw_config, bytes):
                raw_config = raw_config.decode("utf-8")
            config = json.loads(raw_config)
            patch_layer_config(config)
            h5_file.attrs.modify("model_config", json.dumps(config).encode("utf-8"))
        return tf.keras.models.load_model(str(temp_path), compile=False)
    finally:
        temp_path.unlink(missing_ok=True)


def _reconstruct_mobilenetv2_cnn(tf, model_path: Path):
    """Rebuild the known MobileNetV2 head and load H5 weights by layer name."""
    base = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights=None,
    )
    base.trainable = False
    x = tf.keras.layers.GlobalAveragePooling2D(name="global_average_pooling2d")(base.output)
    x = tf.keras.layers.Dropout(0.3, name="dropout")(x)
    output = tf.keras.layers.Dense(15, activation="softmax", name="dense")(x)
    model = tf.keras.Model(base.input, output)
    model.load_weights(str(model_path), by_name=True, skip_mismatch=False)
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
