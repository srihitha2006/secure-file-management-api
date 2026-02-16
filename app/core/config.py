from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # JWT
    JWT_SECRET: str = "change_this_secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # File validation
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_CONTENT_TYPES: str = "application/pdf,image/png,image/jpeg,text/plain"

    # Storage
    STORAGE_DIR: str = "storage"


settings = Settings()
