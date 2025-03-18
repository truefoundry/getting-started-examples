from fastapi import FastAPI
from traceloop.sdk import Traceloop
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()

load_dotenv()

# Ensure APP_NAME environment variable exists
if not os.getenv("APP_NAME"):
    raise ValueError("APP_NAME environment variable is not set")

Traceloop.init(disable_batch=True, 
               app_name=os.getenv("APP_NAME"))

client = OpenAI()

app = FastAPI()

def multiply(a: float, b: float) -> float:
    """Useful for multiplying two numbers."""
    try:
        return a * b
    except TypeError:
        raise TypeError("Arguments must be numbers")

class OpenAIRequest(BaseModel):
    model_name: str = "gpt-4"  # Example: "gpt-4", "gpt-3.5-turbo"
    user_message: str = "What is 5 times 7?"  # Example user query for multiplication

async def generate_openai_response(client, model_name, user_message):
    try:
        if not model_name or len(model_name.strip()) == 0:
            model_name = "gpt-4"  # Fixed typo in model name
        
        if not user_message or len(user_message.strip()) == 0:
            raise ValueError("User message cannot be empty")

        agent = FunctionAgent(
            name="Agent",
            description="Useful for multiplying two numbers",
            tools=[multiply],
            llm=OpenAI(model=model_name),
            system_prompt="You are a helpful assistant that can multiply two numbers.",
        )
        response = await agent.run(user_message)  # Use user_message instead of hardcoded question
        return response

    except Exception as e:
        print(f"Error in generate_openai_response: {str(e)}")
        raise

@app.post("/generate-response", 
    description="Generate a response using OpenAI",
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "response": "The result of 5 times 7 is 35."
                    }
                }
            }
        },
        500: {
            "description": "Error response",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Model not found: gpt-invalid"
                    }
                }
            }
        }
    }
)
async def generate_response(request: OpenAIRequest):
    try:
        response = await generate_openai_response(client, request.model_name, request.user_message)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}, 500