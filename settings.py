from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Book Reader API"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Directory settings
    books_dir: str = "./books_stored"

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./book_app.db"

    # API settings
    api_prefix: str = "/api/v1"

    # File upload settings
    chunk_size: int = 1024 * 1024  # 1MB

    # LLM settings
    default_llm_provider: str = "ollama"
    default_llm_model: str = "gemma3:1b"
    ollama_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def books_path(self) -> Path:
        """Get books directory as Path object."""
        path = Path(self.books_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
