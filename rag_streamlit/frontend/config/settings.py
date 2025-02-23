from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # API Configuration
    PROD_API_URL: str
    DEV_API_URL: str

    # File Upload Configuration
    UPLOAD_DIR: Path = Path("uploaded_files")

    @property
    def is_production(self):
        return self.ENVIRONMENT == "production"

    @property
    def API_URL(self):
        return self.PROD_API_URL if self.is_production else self.DEV_API_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


settings = Settings()
