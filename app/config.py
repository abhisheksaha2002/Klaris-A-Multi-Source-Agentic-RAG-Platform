from pydantic_settings import BaseSettings
import secrets
import warnings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2:1b"
    ollama_embed_model: str = "nomic-embed-text"
    lancedb_uri: str = "./lancedb_data"
    github_token: str = ""

    # JWT signing secret. In .env this is JWT_SECRET_KEY.
    # If left empty, we generate a random one at startup -- safe for local
    # dev (tokens just won't survive a server restart), but in Docker/prod
    # you MUST set this explicitly, or every container restart invalidates
    # all existing logins.
    jwt_secret_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()

if not settings.jwt_secret_key:
    settings.jwt_secret_key = secrets.token_urlsafe(32)
    warnings.warn(
        "JWT_SECRET_KEY not set in .env -- using a random secret generated "
        "for this run only. All users will be logged out on next restart. "
        "Set JWT_SECRET_KEY in .env before deploying.",
        stacklevel=2,
    )
