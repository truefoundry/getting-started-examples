"""RAG pipeline backed by Qdrant vector store and the TrueFoundry LLM Gateway.

Documents are chunked, embedded and stored in a Qdrant collection. At query
time the most similar chunks are retrieved and passed to an LLM to generate a
grounded answer.

Set LOCAL_FAKE_LLM=true to exercise the full Qdrant path without a gateway key.
"""

from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from settings import settings

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know. "
            "Keep the answer concise.\n\nContext:\n{context}",
        ),
        ("human", "{question}"),
    ]
)


class DeterministicFakeEmbeddings(Embeddings):
    """Lightweight local embeddings so Qdrant can be tested without an API key."""

    def __init__(self, size: int):
        self.size = size

    def _embed(self, text: str) -> List[float]:
        values = [0.0] * self.size
        for i, ch in enumerate(text.encode("utf-8")):
            values[i % self.size] += (ch % 31) / 31.0
        norm = sum(v * v for v in values) ** 0.5 or 1.0
        return [v / norm for v in values]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class RAGPipeline:
    def __init__(self, collection_name: str | None = None):
        settings.require_llm_config()
        self.collection_name = collection_name or settings.COLLECTION_NAME
        if settings.LOCAL_FAKE_LLM:
            self.embeddings = DeterministicFakeEmbeddings(size=settings.FAKE_EMBEDDING_SIZE)
            self.llm = None
            self.collection_name = f"{self.collection_name}_fake"
        else:
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.TFY_API_KEY,
                base_url=settings.TFY_LLM_GATEWAY_BASE_URL,
            )
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.TFY_API_KEY,
                base_url=settings.TFY_LLM_GATEWAY_BASE_URL,
            )

        client_kwargs = {
            "url": settings.qdrant_url,
            "prefer_grpc": False,
        }
        if settings.QDRANT_API_PREFIX:
            client_kwargs["prefix"] = settings.QDRANT_API_PREFIX
        if settings.QDRANT_API_KEY:
            client_kwargs["api_key"] = settings.QDRANT_API_KEY

        self.qdrant_client = QdrantClient(**client_kwargs)
        self._ensure_collection(settings.embedding_vector_size)
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def _ensure_collection(self, vector_size: int) -> None:
        existing = {c.name for c in self.qdrant_client.get_collections().collections}
        if self.collection_name in existing:
            return
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def add_documents(self, documents: List[Document]) -> int:
        """Split documents into chunks and index them in Qdrant."""
        chunks = self.text_splitter.split_documents(documents)
        if chunks:
            self.vector_store.add_documents(chunks)
        return len(chunks)

    def retrieve(self, question: str) -> List[Document]:
        return self.vector_store.similarity_search(question, k=settings.SIMILARITY_TOP_K)

    def query(self, question: str) -> dict:
        """Retrieve relevant chunks and generate an answer."""
        docs = self.retrieve(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        if settings.LOCAL_FAKE_LLM:
            answer = (
                f"[local fake llm] Retrieved {len(docs)} chunk(s).\n"
                f"Top context: {docs[0].page_content[:300] if docs else '(none)'}"
            )
        else:
            messages = RAG_PROMPT.invoke({"question": question, "context": context})
            response = self.llm.invoke(messages)
            answer = response.content
        return {
            "answer": answer,
            "sources": [
                {"content": doc.page_content[:500], "metadata": doc.metadata} for doc in docs
            ],
        }

    def delete_collection(self):
        self.qdrant_client.delete_collection(self.collection_name)
