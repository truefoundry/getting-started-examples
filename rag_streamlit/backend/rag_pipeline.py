import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, TypedDict

from config.settings import settings
from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from utils import embeddings, llm

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

load_dotenv()

DEFAULT_COLLECTION_NAME = "document_collection"


@dataclass
class RAGConfig:
    """Configuration settings for the RAG (Retrieval-Augmented Generation) pipeline.

    This class defines the parameters that control the behavior of document processing,
    embedding generation, and query processing in the RAG system.

    Attributes:
        chunk_size (int): The maximum size of text chunks for document splitting (default: 1000)
        chunk_overlap (int): The number of characters to overlap between chunks (default: 200)
        similarity_top_k (int): Number of similar documents to retrieve during search (default: 10)
        embedding_model (str): Name of the embedding model to use (default: "text-embedding-3-large")
        llm_model (str): Name of the language model to use (default: "gpt-4o")
        prompt_template (str): The prompt template ID from LangChain hub (default: "rlm/rag-prompt")
        splitter (str): Text splitter to use ("RecursiveCharacterTextSplitter" or "SemanticChunker")
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_top_k: int = 10
    llm_model: str = settings.LLM_MODEL
    embedding_model: str = settings.EMBEDDING_MODEL
    prompt_template: str = "rlm/rag-prompt"
    splitter: str = "RecursiveCharacterTextSplitter"


class DocumentProcessor:
    """Handles document loading and text splitting operations.

    This class is responsible for loading documents from local storage and splitting them
    into appropriate chunks for processing. It supports both semantic-based and
    character-based text splitting strategies.

    Args:
        config (RAGConfig): Configuration object containing processing parameters
    """

    def __init__(self, config: RAGConfig):
        self.config = config
        if config.splitter == "SemanticChunker":
            self.text_splitter = SemanticChunker(embeddings=embeddings)
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
            )

    def load_local_content(self, directory: str) -> List[Document]:
        """Load and process documents from a local directory.

        Args:
            directory (str): Path to the directory containing documents

        Returns:
            List[Document]: List of loaded LangChain Document objects

        Note:
            Supports various document formats based on DirectoryLoader's capabilities
        """
        loader = DirectoryLoader(directory)
        docs = loader.load()
        return docs


class RAGPipeline:
    """Main implementation of the Retrieval-Augmented Generation (RAG) pipeline.

    This class orchestrates the entire RAG process, including document storage,
    retrieval, and answer generation. It uses a graph-based approach to process
    queries and generate contextually relevant responses.

    The pipeline follows these steps:
    1. Documents are stored in a vector database
    2. When queried, relevant documents are retrieved based on similarity
    3. Retrieved context is combined with the query in a prompt
    4. An LLM generates the final response

    Args:
        config (RAGConfig): Configuration object for the pipeline
    """

    def __init__(self, config: RAGConfig):
        self.config = config
        self._initialize_components()
        self._setup_graph()
        self.rag_prompt = hub.pull(self.config.prompt_template)

    def _initialize_components(self):
        """Initialize core components of the RAG pipeline.

        Sets up:
        - Language Model (LLM)
        - Embedding model
        - Vector store
        - Document processor
        """
        self.llm = llm
        self.embeddings = embeddings
        self.qdrant_vector_store = None
        self.processor = DocumentProcessor(self.config)

    def _setup_graph(self):
        """Configure the processing graph for RAG operations.

        Creates a directed graph that defines the flow of data through the pipeline:
        1. Retrieval node: Fetches relevant documents
        2. Generation node: Produces the final answer
        """

        class State(TypedDict):
            question: str
            context: List[Document]
            answer: str

        def retrieve(state: State):
            if self.qdrant_vector_store is None:
                raise ValueError("Vector store not initialized")
            retrieved_docs = self.qdrant_vector_store.similarity_search(
                state["question"], k=self.config.similarity_top_k
            )
            return {"context": retrieved_docs}

        def generate(state: State):
            docs_content = "\n\n".join(doc.page_content for doc in state["context"])
            messages = self.rag_prompt.invoke({"question": state["question"], "context": docs_content})
            response = self.llm.invoke(messages)
            return {"answer": response.content}

        graph_builder = StateGraph(State).add_sequence([retrieve, generate])
        graph_builder.add_edge(START, "retrieve")
        self.graph = graph_builder.compile()

    def add_documents(self, documents: List[Document]):
        """Add new documents to the vector store for future retrieval.

        Args:
            documents (List[Document]): List of LangChain Document objects to add
        """
        self.qdrant_vector_store.add_documents(documents=documents)

    def query(self, question: str) -> str:
        """Process a query through the RAG pipeline.

        Args:
            question (str): The user's question or query

        Returns:
            str: Generated answer based on the retrieved context

        Example:
            >>> pipeline = RAGPipeline(config)
            >>> answer = pipeline.query("What is RAG?")
        """
        response = self.graph.invoke({"question": question})
        return response["answer"]


# Initialize the RAG pipeline with default configuration
# Re use this pipeline for all the queries
rag_pipeline = RAGPipeline(
    RAGConfig(
        chunk_size=1000,
        chunk_overlap=200,
        similarity_top_k=10,
        embedding_model=settings.EMBEDDING_MODEL,
        llm_model=settings.LLM_MODEL,
    )
)
