from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://codecmp:codecmp@localhost:5432/codecmp"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    upload_dir: str = "/repos"
    max_upload_size_mb: int = 500
    secret_key: str = "change-me-in-production-use-32-random-bytes"
    access_token_expire_minutes: int = 60 * 24  # 24 hours


settings = Settings()
