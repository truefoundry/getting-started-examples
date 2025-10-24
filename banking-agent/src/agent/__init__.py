from dotenv import load_dotenv
from traceloop.sdk import Traceloop
import os
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

load_dotenv()



# Initialize Traceloop
TFY_API_KEY = os.environ.get("TFY_API_KEY")
TRACING_PROJECT_FQN = os.environ.get("TRACING_PROJECT_FQN")
TRACING_APPLICATION_NAME = os.environ.get("TRACING_APPLICATION_NAME")
TRACING_BASE_URL = os.environ.get("TRACING_BASE_URL")

if TRACING_PROJECT_FQN is not None and TRACING_APPLICATION_NAME is not None and TRACING_BASE_URL is not None:
    Traceloop.init(
        api_endpoint=TRACING_BASE_URL,
        headers = {
            "Authorization": f"Bearer {TFY_API_KEY}",
            "TFY-Tracing-Project": TRACING_PROJECT_FQN,
        },
        app_name = TRACING_APPLICATION_NAME,
    )

