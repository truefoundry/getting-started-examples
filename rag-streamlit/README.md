# RAG Document Chat Application

A document chat application that lets you have conversations with your documents using RAG (Retrieval Augmented Generation) method.

## How it Works

### Backend (`/backend`)

The backend uses LangGraph for orchestrating the RAG pipeline:

1. **Document Processing**
   - Documents are uploaded and split into chunks
   - Chunks are embedded and stored in Qdrant vector store
   - Each document gets a unique collection name

2. **RAG Pipeline** (`rag_pipeline.py`)
   - Uses a state-based graph processing flow with two key nodes:
     1. `retrieve`: Fetches semantically similar documents from vector store
     2. `generate`: Produces answers using retrieved context and LLM
   - Document processing capabilities:
     - Supports both semantic chunking (SemanticChunker) and recursive character splitting
     - Configurable chunk size (default: 1000) and overlap (default: 200)
     - DirectoryLoader for handling multiple document formats
   - Vector store integration:
     - Uses Qdrant for document storage and retrieval
     - Configurable similarity search with top-k results (default: 10)
     - Collection-based document organization with UUID naming
   - LLM integration:
     - Configurable model selection (default: GPT-4)
     - Uses LangChain hub prompts (default: "rlm/rag-prompt")
     - Maintains conversation context through state management
   - Key methods:
     - `add_documents()`: Processes and stores new documents
     - `query()`: Executes the RAG pipeline for question answering
     - `_setup_graph()`: Configures the directed processing flow
     - `_initialize_components()`: Sets up LLM, embeddings, and vector store


   ```python
   # Main components
   class RAGPipeline:
       def __init__(self, config, collection_name):
           # Initialize LLM, embeddings, and vector store
           self._setup_graph()  # Sets up LangGraph processing flow

       def query(self, question):
           # 1. Retrieve relevant documents
           # 2. Generate answer using context
           return response
   ```

3. **LangGraph Setup**
   - Creates a directed graph: `retrieve → generate`
   - On every user query, the graph retrieves the most relevant documents from the configured vector database and generates an answer using the configured LLM.

### Frontend (`/frontend`)

A Streamlit application with two main components:

1. **Document Upload**
   - Upload PDF or TXT files
   - Files are processed and stored in the vector database

2. **Chat Interface**
   - Ask questions about the uploaded document
   - View AI-generated responses based on document content

## Quick Start

1. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

   Backend environment variables:
   ```
   QDRANT_API_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_API_PORT=port_number
   QDRANT_API_PREFIX=your_qdrant_prefix
   TFY_API_KEY=your_truefoundry_key
   TFY_LLM_GATEWAY_BASE_URL=your_gateway_url
   ```

   Frontend environment variables:
   ```
   # If ENVIRONMENT is set to 'production', PROD_API_URL will be used
   # If ENVIRONMENT is set to 'development', DEV_API_URL will be used
   ENVIRONMENT=development  # or production
   DEV_API_URL=http://localhost:8000
   PROD_API_URL=https://your-production-api-url
   ```

2. Install dependencies:

   Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

   Frontend:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

3. Start the Services:
   ```bash
   # Start Backend
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000

   # Start Frontend
   cd ../frontend
   streamlit run main.py
   ```

4. Using the Application:
   - Open the Streamlit interface (default: http://localhost:8501)
   - Upload your PDF or TXT file
   - Wait for processing confirmation
   - Start asking questions about your document

## Docker Support

Build and run the services using Docker:

Make sure to configure the environment variables as described in the Quick Start section.

### Backend
```bash
cd backend
docker build -t rag-demo-api .
docker run -p 8000:8000 --env-file .env rag-demo-api
```

### Frontend
```bash
cd frontend
docker build -t rag-demo-frontend .
docker run -p 8501:8501 --env-file .env rag-demo-frontend
```
