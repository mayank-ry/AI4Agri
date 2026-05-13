from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoModelForImageClassification,
    AutoImageProcessor,
    MarianTokenizer,
    MarianMTModel,
)

import os
from pathlib import Path

BASE_CACHE = str(Path(__file__).resolve().parent / "cache")

MODELS = {
    "vit": {
        "path": f"{BASE_CACHE}/vit",
        "model_id": "nateraw/vit-base-beans",
    },
    "translation": {
        "path": f"{BASE_CACHE}/translation",
        "model_id": "Helsinki-NLP/opus-mt-en-hi",
    },
    "flan": {
        "path": f"{BASE_CACHE}/flan",
        "model_id": "google/flan-t5-base",
    },
    "intent": {
        "path": f"{BASE_CACHE}/intent",
        "model_id": "cardiffnlp/twitter-roberta-base-sentiment",
    },
}


def download_vit():
    print("\nDownloading ViT Disease Model...")
    os.makedirs(MODELS["vit"]["path"], exist_ok=True)

    AutoImageProcessor.from_pretrained(
        MODELS["vit"]["model_id"],
        cache_dir=MODELS["vit"]["path"],
    )

    AutoModelForImageClassification.from_pretrained(
        MODELS["vit"]["model_id"],
        cache_dir=MODELS["vit"]["path"],
    )

    print("ViT model downloaded successfully")


def download_translation():
    print("\nDownloading Translation Model...")
    os.makedirs(MODELS["translation"]["path"], exist_ok=True)

    MarianTokenizer.from_pretrained(
        MODELS["translation"]["model_id"],
        cache_dir=MODELS["translation"]["path"],
    )

    MarianMTModel.from_pretrained(
        MODELS["translation"]["model_id"],
        cache_dir=MODELS["translation"]["path"],
    )

    print("Translation model downloaded successfully")


def download_flan():
    print("\nDownloading FLAN-T5 Model...")
    os.makedirs(MODELS["flan"]["path"], exist_ok=True)

    AutoTokenizer.from_pretrained(
        MODELS["flan"]["model_id"],
        cache_dir=MODELS["flan"]["path"],
    )

    AutoModelForSeq2SeqLM.from_pretrained(
        MODELS["flan"]["model_id"],
        cache_dir=MODELS["flan"]["path"],
    )

    print("FLAN-T5 model downloaded successfully")


def download_intent():
    print("\nDownloading Intent Detection Model...")
    os.makedirs(MODELS["intent"]["path"], exist_ok=True)

    AutoTokenizer.from_pretrained(
        MODELS["intent"]["model_id"],
        cache_dir=MODELS["intent"]["path"],
    )

    AutoModelForSequenceClassification.from_pretrained(
        MODELS["intent"]["model_id"],
        cache_dir=MODELS["intent"]["path"],
    )

    print("Intent model downloaded successfully")


if __name__ == "__main__":
    print("\nStarting HuggingFace model downloads...\n")

    download_vit()
    download_translation()
    download_flan()
    download_intent()

    print("\nAll models downloaded successfully!")
