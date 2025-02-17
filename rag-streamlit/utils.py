import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"), api_key=os.getenv("QDRANT_API_KEY")
)

embeddings = OpenAIEmbeddings(
    model="openai-main/text-embedding-ada-002",
    api_key=os.getenv("TFY_API_KEY"),
    base_url=os.getenv("TFY_LLM_GATEWAY_BASE_URL"),
)

llm = ChatOpenAI(
    api_key=os.getenv("TFY_API_KEY"),
    model="openai-main/gpt-4o",
    base_url="https://llm-gateway.truefoundry.com/api/inference/openai",
)

DEFAULT_COLLECTION_NAME = "document_collection"

vector_store = QdrantVectorStore(qdrant_client, DEFAULT_COLLECTION_NAME, embeddings)
