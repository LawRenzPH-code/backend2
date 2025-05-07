# app/core/config.py
import os
from typing import List, Optional
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "MARIS"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:4200", "https://localhost:4200"]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./maris.db")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if os.getenv("ENVIRONMENT") == "test":
            return "sqlite:///./test.db"
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()