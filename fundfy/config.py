"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str = "sk-test-key"
    database_url: str = "sqlite+aiosqlite:///./fundfy.db"
    chroma_persist_dir: str = "./chroma_data"
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    tavily_api_key: str = ""
    generated_files_dir: str = "./generated_files"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
