# Banking Agent using Langraph

This repository contains the code for the banking agent using Langraph. It can be used either via FastAPI or through streamlit.

## Installation

- Make sure you have `uv` installed. If not, refer: https://docs.astral.sh/uv/getting-started/installation/

- Install the dependencies:

```bash
uv sync
```

- Activate the environment:

```bash
source .venv/bin/activate
```

## Environment Variables

Copy the `.env.sample` file to `.env` and update the values according to your setup:

```bash
cp .env.sample .env
```

### Required Environment Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `TFY_API_KEY` | Your TrueFoundry API key for authentication | `your_tfy_api_key_here` |
| `LLM_MODEL` | The LLM model to use | `openai-main/gpt-4o-mini` (default) |
| `LLM_GATEWAY_BASE_URL` | LLM Gateway base URL | `{CONTROL_PLANE_URL}/api/llm` |
| `TFY_SERVICE_ROOT_PATH` | Root path for the FastAPI service (optional) | `` (empty by default) |
| `TRACING_BASE_URL` | OpenTelemetry tracing endpoint | `{CONTROL_PLANE_URL}/api/otel` |
| `TRACING_PROJECT_FQN` | Your tracing project fully qualified name | `your_workspace:your_project` |
| `TRACING_APPLICATION_NAME` | Application name for tracing | `banking-agent` |

**Note:** Replace `{CONTROL_PLANE_URL}` with your actual TrueFoundry control plane URL.

## Running the app

- Run the FastAPI app using

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

- Run the streamlit app using

```bash
streamlit run streamlit_app.py
```

## Deployment on TrueFoundry

To deploy this banking agent on TrueFoundry, follow the comprehensive deployment guide:

[Deploy your first service on TrueFoundry](https://docs.truefoundry.com/docs/deploy-first-service#getting-started-with-deployment)

### Quick Deployment Steps:

1. **Select Workspace**: Choose or create a workspace where you want to deploy the service
2. **Choose Service Type**: Select "Service" since this is a FastAPI application
3. **Source Code**: Choose either GitHub repository or local machine deployment
4. **Configuration**:
   - **Command**: `Please leave empty, will be automatically picked from Dockerfile`
   - **Port**: `8000`
   - **DockerFile**: Use the provided Dockerfile (Dockerfile.streamlit or Dockerfile.fastapi)
5. **Environment Variables**: Set up all the required environment variables as documented above
6. **Deploy**: Submit the deployment form
