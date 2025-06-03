from dotenv import load_dotenv
from traceloop.sdk import Traceloop

load_dotenv()

Traceloop.init(app_name="sateesh-bangking-agent")
