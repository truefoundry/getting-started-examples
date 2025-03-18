# LLM Tracing Example with Truefoundry

## Overview
This project demonstrates how to integrate truefoundry opentelemetry tracing . The application provides an API endpoint to process user queries using OpenAI models and applies tracing to monitor its execution.


## Prerequisites
- Python 3.8+
- A valid OpenAI API key.
- Truefoundry account for tracing.

## Installation

1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd <repo-directory>/llm-tracing
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```sh
   cp .env.sample .env
   ```
   Fill the values
   ```ini
   OPENAI_API_KEY=sk-proj-key
   TRACELOOP_BASE_URL=https://internal.devtest.truefoundry.tech/api/otel
   TRACELOOP_HEADERS="Authorization=Bearer%20<your-url-encoded-jwt>"
   TRACELOOP_METRICS_ENABLED=false
   APP_NAME="<your-app-name>"
   ```

## Running the Application
1. Start the FastAPI server using Uvicorn:
   ```sh
   fastapi dev main.py
   ```
2. The API will be available at: `http://127.0.0.1:8000`

## API Endpoints

### Testing the API
To test the API locally, use the following `curl` command:
```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/generate-response' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model_name": "gpt-4",
  "user_message": "What is 5 times 7?"
}'
```

## Additional Notes
- Ensure that your OpenAI API key is valid.
- If you encounter issues with tracing, verify that Traceloop's base URL and headers are correctly set in the `.env` file.
- The API is designed to process mathematical queries via OpenAI models while demonstrating function-based LLM agent workflows.


