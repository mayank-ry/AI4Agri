from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Centralized configuration management using Pydantic Settings.
    This ensures all env vars are validated at startup.
    """
    PROJECT_NAME: str = "AI4Agri"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Integrations
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: str
    
    GEMINI_API_KEY: str
    
    GEE_SERVICE_ACCOUNT: Optional[str] = None
    GEE_KEY_FILE: str = "test_keys/gee_key.json"
    
    META_WA_TOKEN: Optional[str] = None
    META_WA_PHONE_ID: Optional[str] = None
    
    DISEASE_MODEL_PATH: str = "backend/ml/models/disease_model.h5"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
