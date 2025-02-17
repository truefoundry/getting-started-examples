import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client.http.models import Distance, VectorParams

from rag_pipeline import rag_pipeline
from utils import DEFAULT_COLLECTION_NAME, qdrant_client

app = FastAPI()

UPLOAD_DIR = Path("uploaded_files")
# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


class InitRequest(BaseModel):
    filename: str


@app.post("/init")
async def init_document(request: InitRequest):
    """
    Initializes the vectorstore and the LangGraph inference chain (thread-level persistence).
    Expects:
      - filename: Name of the file in the uploaded_files directory
    """
    try:
        file_path = UPLOAD_DIR / request.filename

        try:
            qdrant_client.create_collection(
                collection_name=DEFAULT_COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
        except Exception as e:
            print(f"Collection {DEFAULT_COLLECTION_NAME} already exists")

        # Load and process the document using the RAG pipeline's processor
        documents = rag_pipeline.processor.load_local_content(str(UPLOAD_DIR))

        # Add to RAG pipeline
        rag_pipeline.add_documents(documents)

        return {"status": "initialized", "filename": request.filename}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing document: {str(e)}"
        )
    finally:
        # Clean up the file
        if file_path.exists():
            os.remove(file_path)


class InferenceRequest(BaseModel):
    query: str


@app.post("/infer")
async def infer(request: InferenceRequest):
    """
    Returns an answer for the given query using the persistent chain.
    The conversation history is maintained automatically (thread-level persistence).
    Ensure you have called /init before calling /infer.
    """
    return {"answer": rag_pipeline.query(request.query)}
