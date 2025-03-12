from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import os
import uuid
import logging
from agent import SQLAndPlotWorkflow, PlotResult, plot_graph
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

app = FastAPI(
    title="SQL and Plot Workflow API",
    description="API for executing SQL queries and generating visualizations",
    version="1.0.0"
)

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

# Initialize the workflow
workflow = SQLAndPlotWorkflow()

@app.post("/query", response_model=WorkflowResponse)
async def execute_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Execute a natural language query to generate SQL and visualizations.
    
    Args:
        request: The query request containing the natural language query
        
    Returns:
        A response with a job ID for tracking the query execution
    """
    job_id = str(uuid.uuid4())
    
    # Initialize the job in the results store
    results_store[job_id] = {
        "status": "processing",
        "events": [],
        "plot_result": None,
        "error": None
    }
    
    # Process the query in the background
    background_tasks.add_task(process_query, job_id, request.query)
    
    return WorkflowResponse(
        job_id=job_id,
        status="processing",
        message="Query is being processed"
    )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a job.
    
    Args:
        job_id: The ID of the job to check
        
    Returns:
        The current status of the job
    """
    if job_id not in results_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = results_store[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        events=job_data["events"],
        plot_result=job_data["plot_result"],
        error=job_data["error"]
    )

@app.get("/plot/{job_id}")
async def get_plot(job_id: str):
    """
    Get the plot image for a completed job.
    
    Args:
        job_id: The ID of the job
        
    Returns:
        The plot image file
    """
    if job_id not in results_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = results_store[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Plot not ready yet")
    
    if not job_data["plot_result"]:
        raise HTTPException(status_code=404, detail="No plot available for this job")
    
    plot_path = job_data["plot_result"].get("plot_path")
    
    if not plot_path or not os.path.exists(plot_path):
        raise HTTPException(status_code=404, detail="Plot file not found")
    
    return FileResponse(plot_path)

@app.get("/graph")
async def get_workflow_graph():
    """
    Generate and return the workflow graph visualization.
    
    Returns:
        The workflow graph image file
    """
    try:
        graph_path = plot_graph()
        return FileResponse(graph_path)
    except Exception as e:
        logger.error(f"Error generating workflow graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating workflow graph: {str(e)}")

async def process_query(job_id: str, query: str):
    """
    Process a query and update the results store.
    
    Args:
        job_id: The ID of the job
        query: The natural language query to process
    """
    try:
        logger.info(f"Processing query for job {job_id}: {query}")
        
        # Execute the workflow
        for response in workflow.run_workflow(query):
            event = response.get("event", "unknown")
            content = response.get("content", {})
            
            # Add the event to the results store
            if isinstance(content, (dict, str)):
                event_content = content
            else:
                # Handle non-dict/str content by converting to dict
                event_content = content.dict() if hasattr(content, "dict") else str(content)
                
            results_store[job_id]["events"].append({
                "event": event,
                "content": event_content
            })
            
            # Update the plot result if available
            if event == "visualization_complete" and isinstance(content, PlotResult):
                results_store[job_id]["plot_result"] = content.dict()
            elif event == "visualization_complete" and isinstance(content, dict):
                results_store[job_id]["plot_result"] = content
            
            # Update the status based on the event
            if event == "workflow_error":
                results_store[job_id]["status"] = "failed"
                results_store[job_id]["error"] = str(content)
            elif event == "workflow_complete":
                results_store[job_id]["status"] = "completed"
        
        # If we get here without setting a final status, mark as completed
        if results_store[job_id]["status"] == "processing":
            results_store[job_id]["status"] = "completed"
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        results_store[job_id]["status"] = "failed"
        results_store[job_id]["error"] = str(e)
        results_store[job_id]["events"].append({
            "event": "workflow_error",
            "content": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 