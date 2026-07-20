"""Deploy Qdrant vector store and the RAG app as Helm applications on TrueFoundry.

Usage:
    pip install truefoundry python-dotenv
    tfy login --host https://<your-org>.truefoundry.cloud
    # Fill deploy vars in the repo-root .env, then:
    python deploy.py
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from truefoundry.deploy import GitHelmRepo, Helm, HelmRepo

logging.basicConfig(level=logging.INFO)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_CANDIDATES = (
    _REPO_ROOT / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(".env"),
)


def _load_dotenv() -> None:
    for env_path in _ENV_CANDIDATES:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return
    load_dotenv(override=False)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise ValueError(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env and set it there."
        )
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def deploy_qdrant() -> None:
    helm = Helm(
        name=_require_env("QDRANT_RELEASE_NAME"),
        source=HelmRepo(
            repo_url=_require_env("QDRANT_HELM_REPO_URL"),
            chart=_require_env("QDRANT_HELM_CHART"),
            version=_require_env("QDRANT_HELM_CHART_VERSION"),
        ),
        values={
            "replicaCount": 1,
            "persistence": {"size": _require_env("QDRANT_PERSISTENCE_SIZE")},
            "resources": {
                "requests": {"cpu": "250m", "memory": "512Mi"},
                "limits": {"cpu": "1", "memory": "1Gi"},
            },
            "service": {"type": "ClusterIP"},
        },
    )
    helm.deploy(workspace_fqn=_require_env("WORKSPACE_FQN"), wait=False)


def deploy_rag_app() -> None:
    image = _require_env("RAG_IMAGE")
    repository, _, tag = image.rpartition(":")
    helm = Helm(
        name=_require_env("RAG_RELEASE_NAME"),
        source=GitHelmRepo(
            repo_url=_require_env("HELM_REPO_URL"),
            revision=_require_env("HELM_REVISION"),
            path=_require_env("HELM_RAG_CHART_PATH"),
        ),
        values={
            "image": {"repository": repository, "tag": tag or "latest"},
            "config": {
                "qdrant": {
                    # In-cluster service name (= Helm release name), not localhost
                    "host": _require_env("QDRANT_RELEASE_NAME"),
                    "port": int(os.getenv("QDRANT_SERVICE_PORT", "6333")),
                    "apiKey": os.getenv("QDRANT_API_KEY", ""),
                    "apiPrefix": os.getenv("QDRANT_API_PREFIX", ""),
                },
                "truefoundry": {
                    "llmGatewayBaseUrl": _require_env("TFY_LLM_GATEWAY_BASE_URL"),
                    "apiKey": _require_env("TFY_API_KEY"),
                    "host": _require_env("TFY_HOST"),
                },
                "llmModel": _require_env("LLM_MODEL"),
                "embeddingModel": _require_env("EMBEDDING_MODEL"),
                "embeddingDimensions": int(_require_env("EMBEDDING_DIMENSIONS")),
                "collectionName": _require_env("COLLECTION_NAME"),
                "chunkSize": int(_require_env("CHUNK_SIZE")),
                "chunkOverlap": int(_require_env("CHUNK_OVERLAP")),
                "similarityTopK": int(_require_env("SIMILARITY_TOP_K")),
                "localFakeLlm": _env_bool("LOCAL_FAKE_LLM", False),
                "fakeEmbeddingSize": int(_require_env("FAKE_EMBEDDING_SIZE")),
            },
        },
    )
    helm.deploy(workspace_fqn=_require_env("WORKSPACE_FQN"), wait=False)


if __name__ == "__main__":
    _load_dotenv()
    try:
        deploy_qdrant()
        deploy_rag_app()
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
