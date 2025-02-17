from dataclasses import dataclass
from typing import List, TypedDict

from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph

from utils import embeddings, llm, vector_store

load_dotenv()

DEFAULT_COLLECTION_NAME = "document_collection"


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_top_k: int = 10
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4o"
    prompt_template: str = "rlm/rag-prompt"
    splitter: str = "RecursiveCharacterTextSplitter"


class DocumentProcessor:
    """Handles document loading and processing"""

    def __init__(self, config: RAGConfig):
        self.config = config
        if config.splitter == "SemanticChunker":
            self.text_splitter = SemanticChunker(embeddings=embeddings)
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )

    def load_local_content(self, directory: str) -> List[Document]:
        """Load and split local content"""
        loader = DirectoryLoader(directory)
        docs = loader.load()
        return docs


class RAGPipeline:
    """Main RAG pipeline implementation"""

    def __init__(self, config: RAGConfig):
        self.config = config
        self._initialize_components()
        self._setup_graph()
        self.rag_prompt = hub.pull(self.config.prompt_template)

    def _initialize_components(self):
        """Initialize LLM, embeddings, and vector store"""
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.processor = DocumentProcessor(self.config)

    def _setup_graph(self):
        """Setup the RAG processing graph"""

        class State(TypedDict):
            question: str
            context: List[Document]
            answer: str

        def retrieve(state: State):
            retrieved_docs = self.vector_store.similarity_search(
                state["question"], k=self.config.similarity_top_k
            )
            return {"context": retrieved_docs}

        def generate(state: State):
            docs_content = "\n\n".join(doc.page_content for doc in state["context"])
            messages = self.rag_prompt.invoke(
                {"question": state["question"], "context": docs_content}
            )
            response = self.llm.invoke(messages)
            return {"answer": response.content}

        graph_builder = StateGraph(State).add_sequence([retrieve, generate])
        graph_builder.add_edge(START, "retrieve")
        self.graph = graph_builder.compile()

    def add_documents(self, documents: List[Document]):
        """Add documents to vector store"""
        self.vector_store.add_documents(documents=documents)

    def query(self, question: str) -> str:
        """Query the RAG pipeline"""
        response = self.graph.invoke({"question": question})
        return response["answer"]


rag_pipeline = RAGPipeline(
    RAGConfig(
        chunk_size=1000,
        chunk_overlap=200,
        similarity_top_k=10,
        embedding_model="text-embedding-3-small",
        llm_model="gpt-4o-mini",
    )
)
