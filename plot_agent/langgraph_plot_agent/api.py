from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Union
import uvicorn
import os
import uuid
from agent import agent
import logging
import json
from models import PlotResult
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import traceback
import sys
import shutil
import matplotlib
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

matplotlib.use('Agg')  # Use non-GUI backend suitable for background tasks

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
# Set logging level to DEBUG for more detailed logs
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from langfuse.callback import CallbackHandler
from dotenv import load_dotenv

load_dotenv('.env')

langfuse_handler = CallbackHandler()

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

app = FastAPI(
    title="SQL and Plot Workflow API",
    description="API for executing SQL queries and generating visualizations",
    version="1.0.0"
)

FastAPIInstrumentor.instrument_app(app)

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
    plot_result: Union[Dict[str, Any], None] = Field(default=None)
    error: Union[str, None] = Field(default=None)

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
    Get the plot image for a job. Will serve the plot if it exists, even if the job status
    is not "completed" (which can happen if the job fails after creating the plot).
    """
    if job_id not in results_store:
        logger.error(f"Job {job_id} not found in results store")
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get the job status and plot result
    job_status = results_store[job_id]["status"]
    plot_result = results_store[job_id]["plot_result"]
    
    logger.info(f"Getting plot for job {job_id}, status: {job_status}, plot_result: {plot_result}")
    
    # Check if we have a plot result with a path
    if not plot_result or "plot_path" not in plot_result or not plot_result["plot_path"]:
        logger.error(f"No valid plot result for job {job_id}")
        raise HTTPException(status_code=400, detail="No plot available for this job")
    
    plot_path = plot_result["plot_path"]
    logger.info(f"Plot path for job {job_id}: {plot_path}")
    
    # Convert relative path to absolute path if necessary
    if not os.path.isabs(plot_path):
        plot_path = os.path.join(PLOTS_DIR, plot_path)
        logger.info(f"Converted to absolute path: {plot_path}")
    
    # Check if the plot file exists
    if not os.path.exists(plot_path):
        # Check if any file in plots directory contains the job_id
        potential_files = [f for f in os.listdir(PLOTS_DIR) if job_id in f]
        if potential_files:
            logger.info(f"Plot file not found at path, but found potential files: {potential_files}")
            plot_path = os.path.join(PLOTS_DIR, potential_files[0])
            logger.info(f"Using alternative plot path: {plot_path}")
        else:
            logger.error(f"Plot file not found at path: {plot_path} and no alternatives found")
            raise HTTPException(status_code=404, detail=f"Plot file not found at path: {plot_path}")
    
    logger.info(f"Serving plot file from: {plot_path}")
    return FileResponse(plot_path)

async def process_query(job_id: str, query: str):
    """
    Process the query in the background using LangGraph agent (non-streaming) and update the results store.
    """
    try:
        # Initialize with the user's message in the correct format
        messages = [HumanMessage(content=query)]
        
        # Track visualization completion
        plot_found = False
        plot_result = None

        try:
            # Invoke the agent to get final output
            final_result = agent.invoke({"messages": messages}, config={"callbacks": [langfuse_handler]})
            
            logger.debug(f"Agent invocation complete. Processing final result messages...")
            
            # First pass: look for explicit plot creation tool results
            for message in final_result["messages"]:
                logger.debug(f"Processing message: {message}")

                if isinstance(message, (AIMessage, BaseMessage)):
                    content = message.content

                    if not isinstance(content, str):
                        try:
                            content = json.dumps(content)
                        except Exception as e:
                            logger.error(f"Error serializing content: {str(e)}")
                            content = str(content)

                    results_store[job_id]["events"].append({
                        "event": message.type,
                        "content": content
                    })

                    # Check for plot creation tool results
                    if message.type == "tool" and isinstance(message.content, dict):
                        tool_content = message.content
                        tool_name = message.name
                        logger.debug(f"Tool execution: {tool_name} with content: {tool_content}")

                        if tool_name == "create_plot" and "plot_path" in tool_content:
                            plot_found = True

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
                                    try:
                                        shutil.copy2(original_path, new_plot_path)
                                        os.remove(original_path)
                                        plot_result["plot_path"] = new_plot_path
                                        logger.info(f"Successfully copied plot to: {new_plot_path}")
                                    except Exception as copy_error:
                                        logger.error(f"Failed to copy plot file: {copy_error}")
                                        # Don't set job to failed here, just log the error
                                        # We'll check the plots directory as a fallback
            
            # If we haven't found a plot yet, check if there are any new plot files in the plots directory
            if not plot_found:
                logger.info(f"No plot found in agent messages. Checking plots directory for recent files...")
                # Get all files in the plots directory sorted by modification time (newest first)
                plot_files = sorted(
                    [f for f in os.listdir(PLOTS_DIR) if f.endswith('.png')],
                    key=lambda f: os.path.getmtime(os.path.join(PLOTS_DIR, f)),
                    reverse=True
                )
                
                if plot_files:
                    newest_plot = plot_files[0]
                    logger.info(f"Found newest plot file: {newest_plot}")
                    
                    # Create a basic plot result
                    plot_result = {
                        "plot_type": "unknown",
                        "plot_path": os.path.join(PLOTS_DIR, newest_plot),
                        "x_col": "",
                        "y_col": "",
                        "title": ""
                    }
                    plot_found = True
                
        except Exception as invoke_error:
            logger.error(f"Error in agent invocation: {str(invoke_error)}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            raise invoke_error

        # Update status after processing
        if plot_found and plot_result:
            results_store[job_id]["status"] = "completed"
            results_store[job_id]["plot_result"] = plot_result
            logger.info(f"Job {job_id} completed successfully with plot: {plot_result['plot_path']}")
        else:
            if results_store[job_id]["error"] is None:
                results_store[job_id]["status"] = "failed"
                results_store[job_id]["error"] = "No visualization created by the agent"
                logger.error(f"Job {job_id} failed: No visualization created by the agent")

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        results_store[job_id]["status"] = "failed"
        results_store[job_id]["error"] = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="debug") 