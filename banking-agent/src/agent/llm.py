import os

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "openai-main/gpt-4o-mini"),
    temperature=0.1,
    max_tokens=256,
    streaming=False,
    api_key=os.getenv("TFY_API_KEY"),
    base_url=os.getenv("LLM_GATEWAY_URL", "https://llm-gateway.truefoundry.com/api/inference/openai"),
)
