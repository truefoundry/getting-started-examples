from fastapi import FastAPI
from openai import OpenAI
from traceloop.sdk import Traceloop
from traceloop.sdk.instruments import Instruments
from dotenv import load_dotenv
import os
from pydantic import BaseModel

from opentelemetry.instrumentation.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()

load_dotenv()

Traceloop.init(disable_batch=True, 
               app_name=os.getenv("APP_NAME"))

client = OpenAI()

app = FastAPI()

class OpenAIRequest(BaseModel):
    model_name: str
    user_message: str

def generate_openai_response(client, model_name, user_message):
    if not model_name:
        model_name = "gpt-4o-mini"
    completion = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": user_message}],
    )
    return completion.choices[0].message.content

@app.post("/generate-response")
def generate_response(request: OpenAIRequest):
    response = generate_openai_response(client, request.model_name, request.user_message)
    return {"response": response}