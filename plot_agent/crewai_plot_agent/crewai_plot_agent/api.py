import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from crewai_plot_agent.crew import CrewaiPlotAgent
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

app = FastAPI(
    title="SQL and Plot Workflow API",
    description="API for executing SQL queries and generating visualizations using CrewAI agents",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store results for retrieval
results_store: Dict[str, Dict[str, Any]] = {}


class QueryRequest(BaseModel):
    query: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    events: List[Dict[str, str]]
    plot_path: Optional[str] = None
    error: Optional[str] = None


async def process_query(job_id: str, query: str):
    """Process the query using CrewAI agents in the background"""
    try:
        # Initialize job status
        results_store[job_id]["events"].append(
            {"event": "processing_start", "content": "Starting query processing with CrewAI agents"}
        )

        # Prepare inputs for CrewAI
        inputs = {"topic": query, "current_year": str(datetime.now().year)}

        # Create plot path for this job
        plot_path = os.path.join(PLOTS_DIR, f"plot_{job_id}.png")

        print(f"Plot path: {plot_path}")

        # Run CrewAI workflow
        crew_agent = CrewaiPlotAgent()
        crew = crew_agent.crew()

        # # Update task configuration to include plot path
        # crew.tasks[1].output_file = plot_path  # Set output file for plot task

        # Run the crew
        result = crew.kickoff(inputs=inputs)

        plot_path = result.pydantic.plot_file_path

        # Check if plot was generated
        if os.path.exists(plot_path):
            results_store[job_id].update(
                {
                    "status": "completed",
                    "events": results_store[job_id]["events"]
                    + [
                        {
                            "event": "processing_complete",
                            "content": "Query processing completed successfully",
                        }
                    ],
                    "plot_path": plot_path,
                }
            )
        else:
            raise Exception("Plot file was not generated")

    except Exception as e:
        # Update results store with error
        results_store[job_id].update(
            {
                "status": "failed",
                "error": str(e),
                "events": results_store[job_id]["events"]
                + [{"event": "processing_error", "content": f"Error during processing: {str(e)}"}],
            }
        )


@app.post("/query", response_model=JobStatusResponse)
async def execute_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Execute a natural language query to analyze and visualize data.
    The query will be processed asynchronously by CrewAI agents.
    """
    job_id = str(uuid.uuid4())

    # Initialize job in the store
    results_store[job_id] = {"status": "processing", "events": [], "plot_path": None, "error": None}

    # Add task to background
    background_tasks.add_task(process_query, job_id, request.query)

    return JobStatusResponse(
        job_id=job_id,
        status="processing",
        events=[{"event": "job_created", "content": "Query processing started"}],
        plot_path=None,
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """Get the status of a query processing job"""
    if job_id not in results_store:
        raise HTTPException(status_code=404, detail="Job not found")

    result = results_store[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=result["status"],
        events=result["events"],
        plot_path=result["plot_path"],
        error=result["error"],
    )


@app.get("/plot/{job_id}")
async def get_plot(job_id: str):
    """Get the plot image for a completed job"""
    print(results_store)
    if job_id not in results_store:
        print(f"Job {job_id} not found in results store")
        raise HTTPException(status_code=404, detail="Job not found")

    if results_store[job_id]["status"] != "completed":
        print(f"Job {job_id} not completed. Status: {results_store[job_id]['status']}")
        raise HTTPException(status_code=400, detail="Job not completed or no plot available")

    if not results_store[job_id]["plot_path"]:
        print(f"No plot result for job {job_id}")
        raise HTTPException(status_code=400, detail="No plot available for this job")

    plot_path = results_store[job_id]["plot_path"]
    print(f"Plot path for job {job_id}: {plot_path}")

    # Convert relative path to absolute path if necessary
    if not os.path.isabs(plot_path):
        plot_path = os.path.join(PLOTS_DIR, plot_path)
        print(f"Converted to absolute path: {plot_path}")

    if not os.path.exists(plot_path):
        print(f"Plot file not found at path: {plot_path}")
        raise HTTPException(status_code=404, detail=f"Plot file not found at path: {plot_path}")

    return FileResponse(plot_path)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
