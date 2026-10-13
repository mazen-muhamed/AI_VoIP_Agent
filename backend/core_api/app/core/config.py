# Application,DB configuration Using Pydantic_Settings
# For (SECRET_KEY, DB, rate limits, CORS)

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8')


    APP_NAME: str = "AI VoIP Agent API"
    APP_VERSION: str = "1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

## From .env file 'Security'
    
    JWT_SECRET: str
    JWT_AlGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 10
    TRUSTED_PROXY_CIDRS: list[str] = []     # empty = never trust X-Forwarded-For, use request.client.host only

# DataBase
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "ai_voip_agent"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])

    # Rate limiting (In memory , we will replace that with Redis)
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 300

# Logging 
    LOG_LEVEL: str = "INFO"


settings = Settings()