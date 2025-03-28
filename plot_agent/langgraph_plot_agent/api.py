from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import os
import uuid
from agent import create_agent, agent
import logging
import json
from models import PlotResult
from langgraph.graph.message import AnyMessage

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv('.env')

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

app = FastAPI(
    title="SQL and Plot Workflow API",
    description="API for executing SQL queries and generating visualizations",
    version="1.0.0"
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store results for retrieval
results_store: Dict[str, Dict[str, Any]] = {}

class QueryRequest(BaseModel):
    query: str
    
class WorkflowResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    events: List[Dict[str, Any]]
    plot_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Initialize the agent
# agent is already imported from agent module

@app.post("/query", response_model=WorkflowResponse)
async def execute_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Execute a natural language query to analyze and visualize data.
    The query will be processed asynchronously.
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job in the store
    results_store[job_id] = {
        "status": "processing",
        "events": [],
        "plot_result": None,
        "error": None
    }
    
    # Add task to background
    background_tasks.add_task(process_query, job_id, request.query)
    
    return WorkflowResponse(
        job_id=job_id,
        status="processing",
        message="Query is being processed. Check status with /status/{job_id}"
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a previously submitted query job.
    """
    if job_id not in results_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=results_store[job_id]["status"],
        events=results_store[job_id]["events"],
        plot_result=results_store[job_id]["plot_result"],
        error=results_store[job_id]["error"]
    )

@app.get("/plot/{job_id}")
async def get_plot(job_id: str):
    """
    Get the plot image for a completed job.
    """
    if job_id not in results_store:
        logger.error(f"Job {job_id} not found in results store")
        raise HTTPException(status_code=404, detail="Job not found")
    
    if results_store[job_id]["status"] != "completed":
        logger.error(f"Job {job_id} not completed. Status: {results_store[job_id]['status']}")
        raise HTTPException(status_code=400, detail="Job not completed or no plot available")
    
    if not results_store[job_id]["plot_result"]:
        logger.error(f"No plot result for job {job_id}")
        raise HTTPException(status_code=400, detail="No plot available for this job")
    
    plot_path = results_store[job_id]["plot_result"]["plot_path"]
    logger.info(f"Plot path for job {job_id}: {plot_path}")
    
    # Convert relative path to absolute path if necessary
    if not os.path.isabs(plot_path):
        plot_path = os.path.join(PLOTS_DIR, plot_path)
        logger.info(f"Converted to absolute path: {plot_path}")
    
    if not os.path.exists(plot_path):
        logger.error(f"Plot file not found at path: {plot_path}")
        raise HTTPException(status_code=404, detail=f"Plot file not found at path: {plot_path}")
    
    return FileResponse(plot_path)

async def process_query(job_id: str, query: str):
    """
    Process the query in the background using LangGraph agent and update the results store.
    """
    try:
        # Initialize with the user's message in the correct format
        messages = [AnyMessage(type="human", content=query, id=str(uuid.uuid4()))]
        config = {"configurable": {"thread_id": job_id}}
        
        # Track visualization completion
        plot_found = False
        plot_result = None
        
        # Stream the agent responses
        for step in agent.stream({"messages": messages}, config=config):
            # Get the state snapshot
            state_snapshot = step["messages"]
            
            if len(state_snapshot) > 0:
                latest_message = state_snapshot[-1]
                
                # Store all agent messages as events
                if latest_message.type in ["assistant", "tool"]:
                    content = latest_message.content
                    
                    # Convert to string if it's not already
                    if not isinstance(content, str):
                        content = json.dumps(content)
                    
                    results_store[job_id]["events"].append({
                        "event": latest_message.type,
                        "content": content
                    })
                    
                    # Check for plot creation tool results
                    if latest_message.type == "tool" and isinstance(latest_message.content, dict):
                        tool_content = latest_message.content
                        tool_name = latest_message.name
                        
                        # Check if this is the result of a plot creation
                        if tool_name == "create_plot" and "plot_path" in tool_content:
                            plot_found = True
                            
                            # Extract plot information 
                            plot_result = {
                                "plot_type": tool_content.get("plot_type", "unknown"),
                                "plot_path": tool_content.get("plot_path", ""),
                                "x_col": tool_content.get("x_col", ""),
                                "y_col": tool_content.get("y_col", ""),
                                "title": tool_content.get("title", "")
                            }
                            
                            # Ensure plot is saved in plots directory with job_id
                            original_path = plot_result["plot_path"]
                            if not os.path.isabs(original_path) and os.path.exists(original_path):
                                new_plot_path = os.path.join(PLOTS_DIR, f"{job_id}_{os.path.basename(original_path)}")
                                
                                try:
                                    os.rename(original_path, new_plot_path)
                                    plot_result["plot_path"] = new_plot_path
                                    logger.info(f"Successfully moved plot to: {new_plot_path}")
                                except Exception as e:
                                    logger.error(f"Failed to move plot file: {e}")
                                    # If rename fails, try to copy the file instead
                                    try:
                                        import shutil
                                        shutil.copy2(original_path, new_plot_path)
                                        os.remove(original_path)  # Clean up original file
                                        plot_result["plot_path"] = new_plot_path
                                        logger.info(f"Successfully copied plot to: {new_plot_path}")
                                    except Exception as copy_error:
                                        logger.error(f"Failed to copy plot file: {copy_error}")
                                        results_store[job_id]["status"] = "failed"
                                        results_store[job_id]["error"] = f"Failed to save plot: {copy_error}"
                
        # After processing all steps, check if a plot was found
        if plot_found and plot_result:
            results_store[job_id]["status"] = "completed"
            results_store[job_id]["plot_result"] = plot_result
        else:
            # Check if there was an error
            if results_store[job_id]["error"] is None:
                results_store[job_id]["status"] = "failed"
                results_store[job_id]["error"] = "No visualization created by the agent"
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        results_store[job_id]["status"] = "failed"
        results_store[job_id]["error"] = str(e)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 