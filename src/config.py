import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"

    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    db_echo: bool = False

    celery_broker_url: str
    celery_result_backend: str

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
