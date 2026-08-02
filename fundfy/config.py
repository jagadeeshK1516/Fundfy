"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./fundfy.db"

    # Redis
    redis_url: str = ""

    # JWT
    jwt_secret: str = "dev-secret-change-in-production-32b"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24  # 24 hours

    # OpenAI
    openai_api_key: str = "sk-test-key"
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_server_url: str = ""

    # Tavily
    tavily_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/integrations/google/callback"

    # Encryption
    encryption_key: str = ""  # Fernet key for token encryption

    # Files
    generated_files_dir: str = "./generated_files"

    # Worker
    background_jobs_enabled: bool = False
    worker_job_timeout: int = 300
    worker_max_retries: int = 3

    # Rate limiting
    rate_limit_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
