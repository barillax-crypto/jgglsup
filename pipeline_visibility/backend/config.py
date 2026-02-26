from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pipeline Visibility Dashboard"
    database_url: str = "sqlite+pysqlite:///./pipeline_visibility.db"
    redis_url: str = "redis://redis:6379/0"
    sync_max_delay_minutes: int = 15
    sync_alert_hours: int = 24

    model_config = SettingsConfigDict(env_prefix="PVD_", env_file=".env", extra="ignore")


settings = Settings()
