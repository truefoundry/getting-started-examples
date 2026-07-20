import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from pydantic import BaseModel
from rag_pipeline import RAGPipeline
from settings import settings

app = FastAPI(
    title="RAG on TrueFoundry with Helm (Qdrant)",
    description="Retrieval-Augmented Generation API backed by Qdrant vector store on TrueFoundry with Helm Chart",
    root_path=settings.TFY_SERVICE_ROOT_PATH,
    docs_url="/",
)

rag_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a .txt or .pdf file, chunks, embeds and indexes it in Qdrant vector store."""
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in (".txt", ".pdf"):
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        loader = PyPDFLoader(tmp_path) if suffix == ".pdf" else TextLoader(tmp_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["source"] = filename

        chunks_indexed = get_pipeline().add_documents(documents)
        return {"status": "indexed", "filename": filename, "chunks_indexed": chunks_indexed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


class QueryRequest(BaseModel):
    query: str


@app.post("/query")
async def query(request: QueryRequest):
    """Answers a question using the indexed documents from Qdrant vector store."""
    try:
        return get_pipeline().query(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering query: {e}")


@app.delete("/documents")
async def delete_documents():
    """Deletes the entire vector collection (all indexed documents)."""
    try:
        get_pipeline().delete_collection()
        global rag_pipeline
        rag_pipeline = None
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting collection: {e}")
