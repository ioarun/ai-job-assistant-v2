from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    langfuse_secret_key: str
    langfuse_public_key: str
    langfuse_base_url: str = "http://localhost:3000"

    database_url: str

    adzuna_app_id: str
    adzuna_api_key: str
    adzuna_country: str = "au"



@lru_cache
def get_settings() -> Settings:
    return Settings()
