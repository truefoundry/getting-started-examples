from dotenv import load_dotenv
from traceloop.sdk import Traceloop
import os
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

load_dotenv()



# Initialize Traceloop
TFY_API_KEY = os.environ.get("TFY_API_KEY")
Traceloop.init(
    api_endpoint=os.environ.get("TRACING_BASE_URL") or "",
    headers = {
        "Authorization": f"Bearer {TFY_API_KEY}",
        "TFY-Tracing-Project": os.environ.get("TRACING_PROJECT_FQN") or "",
    },
    app_name = os.environ.get("TRACING_APPLICATION_NAME") or "",
)
