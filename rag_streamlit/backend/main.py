import os
import shutil
import sys
from pathlib import Path

from config.settings import settings
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from qdrant_client.http.models import Distance, VectorParams
from rag_pipeline import rag_pipeline
from utils import qdrant_client

app = FastAPI()

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
      - file: Uploaded file to process (.txt files only)
    """
    # Validate file extension
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are currently supported")

    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            qdrant_client.create_collection(
                collection_name=settings.DEFAULT_COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
        except Exception as e:
            print(f"Collection {settings.DEFAULT_COLLECTION_NAME} already exists, Re using it")

        # Process only the uploaded file
        documents = rag_pipeline.processor.load_local_content(str(UPLOAD_DIR))

        # Add to RAG pipeline
        rag_pipeline.add_documents(documents)

        return {"status": "initialized", "filename": file.filename}

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
    return {"answer": rag_pipeline.query(request.query)}
