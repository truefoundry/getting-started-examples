import os
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from rag_pipeline import RAGConfig, RAGPipeline

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


global rag_pipeline
rag_pipeline = None


@app.post("/init")
async def init_document(file: UploadFile = File(...)):
    """
    Initializes the vectorstore and the LangGraph inference chain (thread-level persistence).
    Expects:
      - file: Uploaded file to process (.txt or .pdf files)
    """
    global rag_pipeline

    # Validate file extension
    if not file.filename.lower().endswith((".txt", ".pdf")):
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are currently supported")

    try:
        # Extract the file extension
        file_extension = os.path.splitext(file.filename)[1]
        # Generate a unique collection name
        collection_name = f"{uuid.uuid4()}-{file_extension}"
        # Save the uploaded file
        file_path = UPLOAD_DIR / collection_name
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize the RAG pipeline with unique collection name
        rag_pipeline = RAGPipeline(
            config=RAGConfig(),
            collection_name=collection_name,
        )
        # Add the documents to the vector store
        rag_pipeline.add_documents(str(UPLOAD_DIR))

        # Return the status and the filename
        return {"status": "initialized", "collection_name": collection_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        # Remove the uploaded file from the upload directory
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
    # Check if the RAG pipeline is initialized
    if rag_pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="RAG pipeline not initialized. Please upload a file first",
        )

    # Return the answer
    return {"answer": rag_pipeline.query(request.query)}
