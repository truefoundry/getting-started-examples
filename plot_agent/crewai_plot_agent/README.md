# SQL and Plot Workflow API

A powerful data visualization system that uses AI agents to automatically generate SQL queries and create meaningful visualizations from natural language requests. Built with CrewAI framework and deployable on TrueFoundry.

## Architecture Overview

This project consists of several key components working together:

1. **Query Agent**: An AI agent powered by CrewAI that:
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

### Prerequisites

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

1. Install UV:
```bash
pip install uv
```

2. Install CrewAI CLI:
```bash
pip install -U "crewai"
```

### Environment Setup

1. Create a `.env` file in your project root:
```env
OPENAI_API_KEY=your_openai_api_key
CLICKHOUSE_HOST=your_clickhouse_host
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=your_database
CLICKHOUSE_USER=your_user
CLICKHOUSE_PASSWORD=your_password
```

2. Install project dependencies:
```bash
crewai install
```

### Configuration

1. **Agent Configuration**: 
   - Modify `src/crewai_plot_agent/config/agents.yaml` to define your agents
   - Configure agent roles, goals, and backstories

2. **Task Configuration**:
   - Modify `src/crewai_plot_agent/config/tasks.yaml` to define your tasks
   - Set task descriptions and expected outputs

3. **Crew Setup**:
   - Modify `src/crewai_plot_agent/crew.py` to customize agent tools and logic
   - Adjust task dependencies and workflow

### Running the Services

1. Start the CrewAI workflow:
```bash
crewai run
```

2. Start the FastAPI server:
```bash
python api.py
```

3. Start the Streamlit UI (in a new terminal):
```bash
streamlit run app.py
```

## Deployment on TrueFoundry

Follow the same deployment steps as mentioned in the original documentation, with these CrewAI-specific additions:

1. Add CrewAI environment variables to your deployment configuration:
```python
env={
    "OPENAI_API_KEY": "your_openai_api_key",
    "CLICKHOUSE_HOST": "your_clickhouse_host",
    "CLICKHOUSE_PORT": "443",
    "CLICKHOUSE_USER": "your_user",
    "CLICKHOUSE_PASSWORD": "your_password",
    "CLICKHOUSE_DATABASE": "default",
    "CREWAI_VERBOSE": "true"  # For detailed CrewAI logs
},
```

## Support and Resources

For support with CrewAI specific features:
- Visit the [CrewAI documentation](https://docs.crewai.com)
- Join the [CrewAI Discord](https://discord.com/invite/X4JWnZnxPb)
- Chat with [CrewAI docs](https://chatg.pt/DWjSBZn)

For general project support:
- Check the [API documentation](/docs)
- Monitor application health at `/health`
- View metrics at `/metrics`

## API Usage

The API endpoints remain the same as in the original documentation. Refer to the FastAPI documentation at `/docs` for detailed API specifications.

For CrewAI-specific debugging and monitoring, enable verbose mode in your configuration or use the `CREWAI_VERBOSE` environment variable.
