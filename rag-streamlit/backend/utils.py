"""
Utility module for initializing and configuring core components of the RAG system.

This module sets up the following components:
- Qdrant vector database client for storing and retrieving embeddings
- OpenAI embeddings model for converting text to vector representations
- ChatGPT language model for generating responses
- Vector store interface combining Qdrant with the embeddings model
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# from langchain_chroma import Chroma
from config.settings import settings  # noqa: E402
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # noqa: E402
from langchain_qdrant import QdrantVectorStore  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.http.models import Distance, VectorParams  # noqa: E402

# Initialize Qdrant client for vector database operations
qdrant_client = QdrantClient(
    url=settings.QDRANT_API_URL, port=settings.QDRANT_API_PORT, prefix=settings.QDRANT_API_PREFIX
)

# Initialize Chroma client for vector database operations
# chroma_client = HttpClient(
#     host=settings.CHROMADB_API_URL
# )

# Configure embeddings model for converting text to vectors
embeddings = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    api_key=settings.TFY_API_KEY,
    base_url=settings.TFY_LLM_GATEWAY_BASE_URL,
)

# Initialize language model for generating responses
llm = ChatOpenAI(
    api_key=settings.TFY_API_KEY,
    model=settings.LLM_MODEL,
    base_url=settings.TFY_LLM_GATEWAY_BASE_URL,
)


# Create a collection if it doesn't exist
def create_vector_store(collection_name):
    try:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    except Exception:
        print(f"Collection {settings.DEFAULT_COLLECTION_NAME} already exists, Re using it")

    # Create vector store interface combining Qdrant with embeddings
    qdrant_vector_store = QdrantVectorStore(qdrant_client, collection_name, embeddings)
    return qdrant_vector_store
