# For (SECRET_KEY, DB URL, rate limits, CORS)

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8')

    app_name: str = "AI VoIP Agent API"
    app_version: str = "1.0"
    environment: str = "development"
    debug: bool = False

## From .env file
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_AlGORITHM: str = 'HS256'
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_dayes: int = 10
    trusted_proxy_cidrs: list[str] = []         # empty = never trust X-Forwarded-For, use request.client.host only
    CORS_ORIGIN: list[str] = ["http://localhost:5173"] # vite 'frontend'

    admin_username: str
    admin_password: str

settings = Settings()