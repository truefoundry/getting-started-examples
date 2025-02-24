import os
import shutil
import sys
import uuid
from pathlib import Path

from config.settings import settings
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from rag_pipeline import rag_pipeline
from utils import create_vector_store

app = FastAPI(
    title="RAG Pipeline",
    root_path=os.getenv("TFY_SERVICE_ROOT_PATH", ""),
    docs_url="/",
)

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

UPLOAD_DIR = Path("uploaded_files")
# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


class InitRequest(BaseModel):
    filename: str


@app.post("/init")
async def init_document(file: UploadFile = File(...)):
    """
    Initializes the vectorstore and the LangGraph inference chain (thread-level persistence).
    Expects:
      - file: Uploaded file to process (.txt or .pdf files)
    """
    # Validate file extension
    if not file.filename.lower().endswith((".txt", ".pdf")):
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are currently supported")

    try:
        # Generate unique filename with original extension
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize the RAG pipeline with unique collection name
        collection_name = settings.DEFAULT_COLLECTION_NAME + uuid.uuid4().hex
        rag_pipeline.qdrant_vector_store = create_vector_store(collection_name)

        # Process the uploaded file
        documents = rag_pipeline.processor.load_local_content(str(UPLOAD_DIR))

        # Add to RAG pipeline
        rag_pipeline.add_documents(documents)

        return {"status": "initialized", "filename": unique_filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
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
    if rag_pipeline.qdrant_vector_store is None:
        raise HTTPException(
            status_code=400,
            detail="Vector store not initialized. Please upload a file first",
        )

    return {"answer": rag_pipeline.query(request.query)}
