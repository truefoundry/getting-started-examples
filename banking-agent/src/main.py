import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.agent.graph import run_agent

app = FastAPI(
    title="Backend for RAG",
    root_path=os.getenv("TFY_SERVICE_ROOT_PATH", ""),
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health-check")
def status():
    return JSONResponse(content={"status": "OK"})


class UserInput(BaseModel):
    thread_id: str
    user_input: str


@app.post("/run_agent")
async def run_agent_endpoint(user_input: UserInput):
    return await run_agent(user_input.thread_id, user_input.user_input)
