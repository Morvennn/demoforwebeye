"""Runtime configuration, loaded from environment variables / .env."""
# Daniel Design

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MiniMax (OpenAI-compatible API)
    minimax_api_key: str = ""
    # China platform (platform.minimaxi.com) uses api.minimaxi.com; the international
    # endpoint is api.minimax.io. Pick the one that matches your key's region.
    minimax_base_url: str = "https://api.minimaxi.com/v1"
    minimax_model: str = "MiniMax-M3"

    # GitHub (optional; raises rate limit when set)
    github_token: str = ""

    # CORS — frontend origin allowed to call the API. "*" for local dev.
    cors_origin: str = "*"

    # Token-budget tunables for repo sampling
    max_key_files: int = 8
    max_file_chars: int = 6000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
