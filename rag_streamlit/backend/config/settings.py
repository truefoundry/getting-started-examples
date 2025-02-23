from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # API Configuration
    PROD_API_URL: str
    DEV_API_URL: str

    # LLM Gateway Configuration
    TFY_API_KEY: str
    TFY_LLM_GATEWAY_BASE_URL: str

    # Qdrant Vector Store Configuration
    QDRANT_API_URL: str
    QDRANT_API_KEY: str

    # Chroma Vector Store Configuration
    CHROMADB_API_URL: str

    DEFAULT_COLLECTION_NAME: str = "document_collection"

    # LLM Configuration
    LLM_MODEL: str = "openai-main/gpt-4o-mini"
    EMBEDDING_MODEL: str = "openai-main/text-embedding-ada-002"

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
