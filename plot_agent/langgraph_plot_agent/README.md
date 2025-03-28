# SQL and Plot Workflow API

A powerful data visualization system that uses AI agents to automatically generate SQL queries and create meaningful visualizations from natural language requests. Built with LangGraph and deployable on TrueFoundry.

## Architecture Overview

This project consists of several key components working together:

1. **LangGraph Agent**: A unified AI agent powered by LangGraph that:
   - Uses GPT-4 for natural language understanding
   - Orchestrates the workflow between SQL query generation and visualization
   - Handles data extraction and preprocessing
   - Manages the state and flow of the conversation

2. **Tools Integration**:
   - `execute_clickhouse_query`: Handles SQL query execution against ClickHouse database
   - `create_plot`: Generates visualizations using matplotlib/seaborn

3. **FastAPI Backend**: RESTful API that:
   - Coordinates the agent workflow
   - Manages asynchronous job processing
   - Serves plot images and results

4. **Streamlit Frontend**: User interface that:
   - Provides an intuitive query interface
   - Displays real-time processing status
   - Shows interactive visualizations
   - Allows plot customization

## Data Flow

1. User submits a natural language query through Streamlit UI
2. Query is processed by the LangGraph agent
3. Agent orchestrates between SQL execution and visualization tools
4. Results are displayed in Streamlit UI

## Setup and Installation

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your actual credentials:
```env
# Truefoundry LLMGateway Configuration
LLM_GATEWAY_BASE_URL=your_llm_gateway_base_url_here
LLM_GATEWAY_API_KEY=your_llm_gateway_api_key_here
MODEL_ID=openai-main/gpt-4o  # Format: provider-name/model-name

# ClickHouse Database Configuration
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=443
CLICKHOUSE_USER=your_clickhouse_user_here
CLICKHOUSE_PASSWORD=your_clickhouse_password_here
CLICKHOUSE_DATABASE=default
```

### 3. Agent Implementation

The project uses LangGraph for agent implementation. Here's how it's configured:

```python
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import Annotated, TypedDict

# Define the state structure
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Create the agent
def create_agent():
    builder = StateGraph(State)
    
    # Initialize LLM with TrueFoundry configuration
    llm = ChatOpenAI(
        model=os.getenv("MODEL_ID"),
        api_key=os.getenv("LLM_GATEWAY_API_KEY"),
        base_url=os.getenv("LLM_GATEWAY_BASE_URL"),
        streaming=True
    )
    
    # Bind tools to LLM
    llm.bind_tools(tools_list)
    
    # Define nodes and edges
    builder.add_node("assistant", llm)
    builder.add_node("tools", ToolNode(tools_list))
    
    # Configure the graph flow
    builder.add_edge(START, "assistant")
    builder.add_edge("tools", "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition_modified,
    )
    builder.add_edge("assistant", "__end__")
    
    return builder.compile()
```

### 4. Start the Services

```bash
# Start FastAPI server
python api.py

# Start Streamlit UI (in a new terminal)
streamlit run app.py
```

## Deployment on TrueFoundry

### Prerequisites

1. Install TrueFoundry CLI:
```bash
pip install -U "truefoundry"
```

2. Login to TrueFoundry:
```bash
tfy login --host "https://app.truefoundry.com"
```

### Deployment Steps

1. Navigate to the Deployments section in TrueFoundry.

2. Click Service at the bottom.

3. Select your cluster workspace.

4. You can deploy from your laptop, GitHub, or Docker. If deploying from your laptop, ensure you have completed the prerequisites above.

5. The TrueFoundry platform will generate a `deploy.py` file and add it to your project. The environment variables will be automatically loaded from your `.env` file during deployment.

6. Run the deployment command:
```bash
python deploy.py
```

Your SQL and Plot Workflow API is now deployed and running on TrueFoundry!

7. To confirm everything is working, you can send a test query using curl:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "Show me the cost trends by model over the last week"}' \
  https://your-service-url.truefoundry.cloud/query
```

If everything is set up correctly, you should receive a response with a job ID that you can use to track the status of your query.

### Monitoring and Management

1. Access the TrueFoundry dashboard to:
   - Monitor resource usage
   - View application logs
   - Scale resources as needed
   - Configure auto-scaling rules

2. Check application health:
   - Backend health: `/health`
   - API documentation: `/docs`
   - Metrics: `/metrics`

## Example Usage

1. **Submit a Query via API**:
```bash
curl -X POST "https://your-service-url.truefoundry.cloud/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me the cost trends by model over the last week"}'
```

2. **Via Streamlit UI**:
   - Navigate to the UI URL
   - Enter your query in the text input
   - View real-time query processing and results

## API Endpoints

### 1. Submit a Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the cost trends by model over the last week. Filter models that show a 0 cost."}'
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Query is being processed. Check status with /status/{job_id}"
}
```

### 2. Check Job Status

```bash
curl -X GET http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "events": [
    {
      "event": "query_start",
      "content": "Processing query..."
    },
    {
      "event": "sql_execution",
      "content": "Executing SQL query..."
    },
    {
      "event": "visualization",
      "content": "Creating visualization..."
    },
    {
      "event": "complete",
      "content": "Query completed successfully"
    }
  ]
}
```

### **Deploying Streamlit Separately**
To ensure proper communication between FastAPI and Streamlit, you need to deploy Streamlit as a **separate service** on the TrueFoundry platform.

#### **1. Separate Deployment for Streamlit**
Deploy the Streamlit frontend separately from FastAPI on TrueFoundry.

#### **2. Configure CORS in FastAPI**
To allow the frontend to communicate with FastAPI, add **CORS (Cross-Origin Resource Sharing)** to your FastAPI backend:

Modify your `api.py` to include:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **3. Define an Environment Variable in Streamlit**
Your Streamlit application should use an environment variable to point to the FastAPI backend:

In your **Streamlit environment** configuration:

```bash
FASTAPI_ENDPOINT="https://your-service-url.truefoundry.cloud"
```

Then, modify your **Streamlit app** to read this environment variable:

```python
import os

FASTAPI_ENDPOINT = os.getenv("FASTAPI_ENDPOINT", "http://localhost:8000")
```

This ensures that Streamlit dynamically references the correct FastAPI instance.

#### **4. Use Separate Ports**
If deploying locally or if TrueFoundry does not handle port conflicts automatically, ensure **FastAPI and Streamlit run on separate ports**.

Example:
 - **FastAPI**: `https://your-service-url.truefoundry.cloud`
 - **Streamlit**: `https://your-streamlit-url.truefoundry.cloud`

To run Streamlit on a different port locally:

```bash
streamlit run app.py --server.port 8501
```

### **Final Notes**
After deploying both services, make sure to:
 - Test API connectivity from Streamlit to FastAPI
 - Update Streamlit's `.env` file with the correct FastAPI endpoint
 - Confirm CORS settings allow requests from Streamlit

This ensures your SQL and Plot Workflow API functions properly across both services.