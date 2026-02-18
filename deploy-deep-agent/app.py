"""FastAPI backend for Content Builder Agent."""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import the new run_content_agent function
from content_agent import run_content_agent, OUTPUT_DIR

app = FastAPI(
    title="Content Builder Agent Backend",
    root_path=os.getenv("TFY_SERVICE_ROOT_PATH", ""),
    docs_url="/",
)

# CORS middleware for local development/different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files (markdown + images)
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")

@app.get("/health-check")
def status():
    """Health check endpoint to verify service status."""
    return JSONResponse(content={"status": "OK"})


class UserInput(BaseModel):
    """Request model for user input to the agent."""
    thread_id: str
    user_input: str

@app.post("/run_agent")
async def run_agent_endpoint(user_input: UserInput):
    """
    Receives user input and executes the content builder agent to provide a response.
    """
    out = await run_content_agent(user_input.thread_id, user_input.user_input)

    # Optional: If your prompt always uses a slug, you can return expected URLs.
    # If not, you can parse tool outputs to detect written paths.
    return {
        "thread_id": user_input.thread_id,
        "final_text": out["final_text"],
        "platform": out.get("platform"),
        "slug": out.get("slug"),
        "files": out.get("files", {})
        }