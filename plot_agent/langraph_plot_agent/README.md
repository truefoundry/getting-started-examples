# SQL and Plot Workflow with LangGraph

This project demonstrates a workflow for executing SQL queries and generating visualizations using natural language queries. It uses LangGraph for creating a stateful agent workflow.

## Architecture

The application is built using the following components:

1. **LangGraph Workflow**: A directed graph with nodes for SQL query generation and visualization creation.
2. **FastAPI Backend**: Provides REST API endpoints for submitting queries and retrieving results.
3. **Streamlit Frontend**: A user-friendly interface for interacting with the workflow.

## LangGraph Implementation

The workflow is implemented using LangGraph, which provides a structured way to build stateful agents with clear transitions between different components. The workflow consists of the following nodes:

- **SQL Agent**: Generates and executes SQL queries based on natural language input.
- **Plot Agent**: Creates visualizations based on the SQL query results.

The workflow graph is defined using the `StateGraph` class from LangGraph, with conditional edges that determine the flow between nodes.

## Workflow State

The workflow maintains a state object that includes:

- **query**: The original natural language query
- **sql_result**: The result of the SQL query
- **viz_request**: The visualization request
- **plot_result**: The result of the plot generation
- **error**: Any error that occurred during the workflow
- **messages**: The conversation history
- **next**: The next node to execute

## Running the Application

### Prerequisites

- Python 3.8+
- ClickHouse database
- OpenAI API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   CLICKHOUSE_HOST=your_clickhouse_host
   CLICKHOUSE_PORT=your_clickhouse_port
   CLICKHOUSE_USER=your_clickhouse_user
   CLICKHOUSE_PASSWORD=your_clickhouse_password
   CLICKHOUSE_DATABASE=your_clickhouse_database
   ```

### Running the API

```
python api.py
```

### Running the Streamlit App

```
streamlit run app.py
```

## API Endpoints

- **POST /query**: Submit a natural language query
- **GET /status/{job_id}**: Get the status of a job
- **GET /plot/{job_id}**: Get the plot image for a completed job
- **GET /graph**: Get the workflow graph visualization

## Visualization

The application can generate various types of visualizations:

- Bar charts
- Line charts
- Scatter plots
- Histograms
- Box plots
- Violin plots

## Example Queries

- Show me the cost trends by model over the last week
- Compare usage patterns across different models
- Display daily active users over time
- Analyze error rates by model type
- Show me the distribution of latency by model
- What are the top 5 models by cost?

## LangGraph Workflow Visualization

The application includes a feature to visualize the LangGraph workflow. This helps in understanding the flow of data and the decision-making process of the agent.

## License

MIT