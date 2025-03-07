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

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
CLICKHOUSE_HOST=your_clickhouse_host
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=your_database
CLICKHOUSE_USER=your_user
CLICKHOUSE_PASSWORD=your_password
```

### 3. Agent Implementation

The project uses two Agno agents. Here's how they're configured:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from plot_tools import PlotTools
from query_tools import QueryTools

# Query Agent for SQL generation
query_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[QueryTools()],
    markdown=True
)

# Visualization Agent for plot generation
viz_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[PlotTools()],
    markdown=True
)
```

### 4. Start the Services

```bash
# Start FastAPI server
uvicorn api:app --reload --port 8000

# Start Streamlit UI (in a new terminal)
streamlit run streamlit_app.py
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

1. **Create deploy.py**

```python
from truefoundry import create_deployment

deployment = create_deployment(
    name="plot-agent",
    workspace_fqn="<your-workspace>",
    environment_variables={
        "OPENAI_API_KEY": "your_openai_api_key",
        "CLICKHOUSE_HOST": "your_clickhouse_host",
        "CLICKHOUSE_PORT": "9000",
        "CLICKHOUSE_DB": "your_database",
        "CLICKHOUSE_USER": "your_user",
        "CLICKHOUSE_PASSWORD": "your_password"
    },
    resources={
        "cpu": "1000m",
        "memory": "2Gi"
    },
    ports=[
        {"port": 8000, "protocol": "http"}  # FastAPI
    ],
    command="uvicorn api:app --host 0.0.0.0 --port 8000"
)

# Deploy Streamlit UI separately
ui_deployment = create_deployment(
    name="plot-agent-ui",
    workspace_fqn="<your-workspace>",
    environment_variables={
        "API_URL": "http://plot-agent:8000"  # Internal service URL
    },
    ports=[
        {"port": 8501, "protocol": "http"}  # Streamlit
    ],
    command="streamlit run streamlit_app.py"
)
```

2. **Deploy the Application**

```bash
python deploy.py
```

3. **Access Your Application**

- FastAPI Backend: `https://plot-agent-8000.your-workspace.truefoundry.cloud`
- Streamlit UI: `https://plot-agent-ui-8501.your-workspace.truefoundry.cloud`

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
      "content": {
        "plot_type": "line",
        "plot_path": "plot.png",
        "x_col": "created_at",
        "y_col": "cost",
        "title": "Cost Trends by Model"
      }
    }
  ],
  "plot_result": {
    "plot_type": "line",
    "plot_path": "plot.png",
    "x_col": "created_at",
    "y_col": "cost",
    "title": "Cost Trends by Model"
  },
  "error": null
}
```

### 3. Get Plot Image

```bash
curl -X GET http://localhost:8000/plot/123e4567-e89b-12d3-a456-426614174000 --output plot.png
```

This will download the plot image to your local machine.

## Project Structure

```
plot_agent/
├── api.py                 # FastAPI application
├── streamlit_app.py       # Streamlit UI
├── plot_tools.py          # Visualization agent tools
├── query_tools.py         # Query agent tools
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
└── README.md             # Documentation
```

## Development

### Adding New Plot Types

1. Add new plot function in `plot_tools.py`
2. Update the Visualization Agent's capabilities
3. Add new plot type to Streamlit UI options

### Extending Query Capabilities

1. Enhance Query Agent's prompt in `query_tools.py`
2. Add new SQL templates if needed
3. Update documentation with new query examples

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Your License Information]

## Interactive API Documentation

FastAPI provides interactive API documentation. Visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 