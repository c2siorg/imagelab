from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3100"]
    database_url: str = "postgresql://postgres:postgres@localhost:5432/imagelab_db"
    debug: bool = False

    model_config = {
        "env_file": ".env",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
