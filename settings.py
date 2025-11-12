from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Book Reader API"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Directory settings
    books_dir: str = "./books_stored"

    # Database settings (example)
    # database_url: Optional[str] = None

    # API settings
    api_prefix: str = "/api/v1"

    # Security settings (example)
    # secret_key: str = "your-secret-key-change-in-production"
    # algorithm: str = "HS256"
    # access_token_expire_minutes: int = 30

    # File upload settings
    # max_upload_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 1024 * 1024  # 1MB
    dict_base_url: str = "https://api.dictionaryapi.dev/api/v2/entries/en/" #just add a word
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def books_path(self) -> Path:
        """Get books directory as Path object"""
        path = Path(self.books_dir)
        path.mkdir(parents=True, exist_ok=True)  # Create if doesn't exist
        return path


# Create a singleton instance
settings = Settings()