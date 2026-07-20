import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (preferred) or next to this file / CWD
_ENV_CANDIDATES = (
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(".env"),
)


def _load_dotenv() -> None:
    for env_path in _ENV_CANDIDATES:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return
    load_dotenv(override=False)


_load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise ValueError(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env and set it there."
        )
    return value


def _env_bool(name: str) -> bool:
    raw = _require_env(name)
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str) -> int:
    return int(_require_env(name))


class Settings:
    def __init__(self) -> None:
        # --- Qdrant vector store ---
        self.QDRANT_HOST = _require_env("QDRANT_HOST")
        self.QDRANT_PORT = _env_int("QDRANT_PORT")
        # Optional API key (empty when Qdrant auth is disabled)
        self.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        # Optional URL prefix when Qdrant is behind a reverse proxy
        self.QDRANT_API_PREFIX = os.getenv("QDRANT_API_PREFIX", "")

        # --- TrueFoundry LLM Gateway ---
        self.TFY_API_KEY = os.getenv("TFY_API_KEY", "")
        self.TFY_LLM_GATEWAY_BASE_URL = os.getenv("TFY_LLM_GATEWAY_BASE_URL", "")
        self.WORKSPACE_FQN = os.getenv("WORKSPACE_FQN", "")
        self.TFY_SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "")

        # --- LLM model ---
        self.LLM_MODEL = _require_env("LLM_MODEL")
        self.EMBEDDING_MODEL = _require_env("EMBEDDING_MODEL")
        # Must match the embedding model output size (e.g. 1536 for text-embedding-3-small)
        self.EMBEDDING_DIMENSIONS = _env_int("EMBEDDING_DIMENSIONS")

        # --- RAG configuration ---
        self.COLLECTION_NAME = _require_env("COLLECTION_NAME")
        self.CHUNK_SIZE = _env_int("CHUNK_SIZE")
        self.CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP")
        self.SIMILARITY_TOP_K = _env_int("SIMILARITY_TOP_K")

        self.LOCAL_FAKE_LLM = _env_bool("LOCAL_FAKE_LLM")
        self.FAKE_EMBEDDING_SIZE = _env_int("FAKE_EMBEDDING_SIZE")

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    @property
    def embedding_vector_size(self) -> int:
        return self.FAKE_EMBEDDING_SIZE if self.LOCAL_FAKE_LLM else self.EMBEDDING_DIMENSIONS

    def require_llm_config(self) -> None:
        if self.LOCAL_FAKE_LLM:
            return
        missing = [
            name
            for name, value in (
                ("TFY_API_KEY", self.TFY_API_KEY),
                ("TFY_LLM_GATEWAY_BASE_URL", self.TFY_LLM_GATEWAY_BASE_URL),
                ("WORKSPACE_FQN", self.WORKSPACE_FQN),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required LLM Gateway settings: {', '.join(missing)}. "
                "Copy .env.example to .env and fill them in, or set LOCAL_FAKE_LLM=true."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
