# RAG Document Chat Application

A document chat application built with FastAPI and Streamlit that enables interactive conversations with your documents using RAG (Retrieval Augmented Generation) technology.

## Features

- 📄 Support for multiple document formats (PDF, TXT, DOC)
- 🔍 Semantic search using Qdrant vector store
- 💬 Interactive chat interface with Streamlit
- 🚀 FastAPI backend for efficient processing
- 🧠 Advanced RAG pipeline with LangGraph

## Quick Start

1. Set up environment variables:

```bash
cp .env.example .env
```


1. Set up environment variables:
```
QDRANT_API_URL=your_qdrant_url  # Can use any vector store
TFY_API_KEY=your_truefoundry_key
TFY_LLM_GATEWAY_BASE_URL=your_gateway_url
```

2. Install dependencies:
```
pip install -r requirements.txt
```


3. Run the application:
```
# Start API
uvicorn api:app --host 0.0.0.0 --port 8000

# Start Frontend
streamlit run streamlit_app.py
```


## Docker Support

# API
docker build -f Dockerfile.api -t rag-demo-api .
docker run -p 8000:8000 rag-demo-api

# Frontend
docker build -f Dockerfile.streamlit -t rag-demo-frontend .
docker run -p 8501:8501 rag-demo-frontend
