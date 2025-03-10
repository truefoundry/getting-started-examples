# SQL and Plot Workflow API

A powerful data visualization system that uses AI agents to automatically generate SQL queries and create meaningful visualizations from natural language requests. Built with Agno framework and deployable on TrueFoundry.

## Architecture Overview

This project consists of several key components working together:

1. **Query Agent**: An AI agent powered by Agno that:
   - Uses GPT-4o for natural language understanding
   - Generates appropriate SQL queries for ClickHouse
   - Handles data extraction and preprocessing
   - Validates query safety and performance

2. **Visualization Agent**: A second AI agent that:
   - Analyzes the data structure and content
   - Determines the most appropriate visualization type
   - Generates plots using matplotlib/seaborn
   - Handles formatting and styling of visualizations

3. **FastAPI Backend**: RESTful API that:
   - Coordinates between agents
   - Manages asynchronous job processing
   - Serves plot images and results

4. **Streamlit Frontend**: User interface that:
   - Provides an intuitive query interface
   - Displays real-time processing status
   - Shows interactive visualizations
   - Allows plot customization

## Data Flow

1. User submits a natural language query through Streamlit UI
2. Query is processed by the Query Agent to generate SQL
3. SQL is executed against ClickHouse database
4. Results are passed to Visualization Agent
5. Visualization Agent creates appropriate plots
6. Results are displayed in Streamlit UI

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

# ClickHouse Database Configuration
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=443
CLICKHOUSE_USER=your_clickhouse_user_here
CLICKHOUSE_PASSWORD=your_clickhouse_password_here
CLICKHOUSE_DATABASE=default
```

### 3. Agent Implementation

The project uses two Agno agents. Here's how they're configured:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from plot_tools import PlotTools
from query_tools import QueryTools

# Query Agent for SQL generation
    sql_agent: Agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        description="",
        instructions=[
        ],
        tools=[ClickHouseTools()],
        show_tool_calls=True,
        markdown=True,
        response_model=SQLQueryResult,
        structured_outputs=True,
    )

# Visualization Agent for plot generation
    plot_agent: Agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        description="",
        instructions=[
        ],
        tools=[PlotTools()],
        markdown=True,
        response_model=VisualizationRequest,
        structured_outputs=True,
    )
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
  https://agno-plot-agent-demo-8000.aws.demo.truefoundry.cloud/query
```

If everything is set up correctly, you should receive a response like:

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Query is being processed. Check status with /status/{job_id}"
}
```

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
curl -X POST "https://plot-agent-8000.your-workspace.truefoundry.cloud/query" \
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
      "event": "sql_query_start",
      "content": "Generating SQL query..."
    },
    {
      "event": "sql_query_complete",
      "content": "SQL query executed successfully"
    },
    {
      "event": "visualization_start",
      "content": "Creating visualization..."
    },
    {
      "event": "visualization_complete",
      "content": "Visualization created successfully"
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
FASTAPI_ENDPOINT="https://agno-plot-agent-demo-8000.aws.demo.truefoundry.cloud"
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
 - **FastAPI**: `https://agno-plot-agent-demo-8000.aws.demo.truefoundry.cloud`
 - **Streamlit**: `https://agno-streamlit-demo-8501.aws.demo.truefoundry.cloud`

To run Streamlit on a different port locally:

```bash
streamlit run app.py --server.port 8501
```

### **Final Notes**
After deploying both services, make sure to:
 - Test API connectivity from Streamlit to FastAPI.
 - Update Streamlit's `.env` file with the correct FastAPI endpoint.
 - Confirm CORS settings allow requests from Streamlit.

This ensures your SQL and Plot Workflow API functions properly across both services.