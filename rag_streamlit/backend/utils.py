"""
Utility module for initializing and configuring core components of the RAG system.

This module sets up the following components:
- Qdrant vector database client for storing and retrieving embeddings
- OpenAI embeddings model for converting text to vector representations
- ChatGPT language model for generating responses
- Vector store interface combining Qdrant with the embeddings model
"""

from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from config.settings import settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
# from langchain_chroma import Chroma
from chromadb import HttpClient

# Initialize Qdrant client for vector database operations
qdrant_client = QdrantClient(
    url=settings.QDRANT_API_URL,
    api_key=settings.QDRANT_API_KEY
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

# Create vector store interface combining Qdrant with embeddings
qdrant_vector_store = QdrantVectorStore(
    qdrant_client, settings.DEFAULT_COLLECTION_NAME, embeddings
)

# Create vector store interface combining Chroma with embeddings
# chroma_vector_store = Chroma(
#     chroma_client, settings.DEFAULT_COLLECTION_NAME, embeddings
# )
