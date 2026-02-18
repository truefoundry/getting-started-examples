# content_agent.py
import os
import base64
from pathlib import Path
from typing import Literal, Optional, Dict, Any
import yaml

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from openai import OpenAI

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).parent  # code directory (AGENTS.md, skills/, subagents.yaml live here)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/tmp/outputs")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

tfy_base_url = os.environ["TFY_BASE_URL"]
tfy_api_key = os.environ["TFY_API_KEY"]
image_model = os.environ["IMAGE_MODEL"]
main_llm_model = os.environ["MAIN_LLM_MODEL"]

# Web search tool for the researcher subagent
@tool
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news"] = "general",
) -> dict:
    """Search the web for current information.

    Args:
        query: The search query (be specific and detailed)
        max_results: Number of results to return (default: 5)
        topic: "general" for most queries, "news" for current events

    Returns:
        Search results with titles, URLs, and content excerpts.
    """
    try:
        from tavily import TavilyClient

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return {"error": "TAVILY_API_KEY not set"}

        client = TavilyClient(api_key=api_key)
        return client.search(query, max_results=max_results, topic=topic)
    except Exception as e:
        return {"error": f"Search failed: {e}"}


@tool
def write_file(content: str, platform: str, slug: str) -> str:
    """Write content to a file.

    Args:
        content: The content to write to the file.
        platform: Either "blogs", "linkedin", "tweets" or "research"
        slug: Blog post slug. Content saves to <platform>/<slug>/post.md 


    """
    output_path = OUTPUT_DIR / platform / slug / "post.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    return f"File written successfully to {output_path}"


@tool
def generate_cover(prompt: str, slug: str) -> str:
    """Generate a cover image for a blog post.

    Args:
        prompt: Detailed description of the image to generate.
        slug: Blog post slug. Image saves to blogs/<slug>/hero.png
    """

    try:
        client = OpenAI(
            api_key = tfy_api_key,
            base_url=tfy_base_url,
        )

        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        for part in response.data:
            if hasattr(part, 'url') and part.url:
                print(f"Image URL: {part.url}")
            if hasattr(part, 'b64_json') and part.b64_json:
                image_bytes = base64.b64decode(part.b64_json)
                
                output_path = OUTPUT_DIR / "blogs" / slug / "hero.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                    return f"Image saved to {output_path}"

        return "No image generated"
    except Exception as e:
        return f"Error: {e}"


@tool
def generate_social_image(prompt: str, platform: str, slug: str) -> str:
    """Generate an image for a social media post.

    Args:
        prompt: Detailed description of the image to generate.
        platform: Either "linkedin" or "tweets"
        slug: Post slug. Image saves to <platform>/<slug>/image.png
    """
    try:

        client = OpenAI(
            api_key = tfy_api_key,
            base_url=tfy_base_url
        )

        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        for part in response.data:
            if hasattr(part, 'url') and part.url:
                print(f"Image URL: {part.url}")
            if hasattr(part, 'b64_json') and part.b64_json:
                image_bytes = base64.b64decode(part.b64_json)
                
                output_path = OUTPUT_DIR / platform / slug / "image.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                    return f"Image saved to {output_path}"

        return "No image generated"
    
    except Exception as e:
        return f"Error: {e}"
    
def _make_llm(model_id: str) -> ChatOpenAI:
    # Prefer this style; your model_kwargs extra_headers approach sometimes works,
    # but default_headers/streaming is the correct/robust way.
    return ChatOpenAI(
            model=model_id,
            api_key=tfy_api_key,
            base_url=tfy_base_url,
            model_kwargs={
            "stream": False,
            "extra_headers":{
                "X-TFY-METADATA": '{}',
                "X-TFY-LOGGING-CONFIG": '{"enabled": true}',
                # "X-TFY-GUARDRAILS": '{"llm_input_guardrails":["guardrails/pii-guardrail"],"llm_output_guardrails":["guardrails/content-moderation-guardrail"]}',
            },
            },
        )

def load_subagents(config_path: Path) -> list:
    available_tools = {"web_search": web_search, "write_file": write_file}
    config = yaml.safe_load(config_path.read_text())

    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
            "model": _make_llm(spec["model"]),
        }
        if "tools" in spec:
            subagent["tools"] = [available_tools[t] for t in spec["tools"]]
        subagents.append(subagent)
    return subagents


_AGENT = None

def get_agent():
    global _AGENT
    if _AGENT is None:
        _AGENT = create_deep_agent(
            model=_make_llm(main_llm_model),
            memory=[str(BASE_DIR / "AGENTS.md")],
            skills=[str(BASE_DIR / "skills")],
            tools=[write_file, generate_cover, generate_social_image],
            subagents=load_subagents(BASE_DIR / "subagents.yaml"),
            backend=FilesystemBackend(root_dir=BASE_DIR),
        )
    return _AGENT


async def run_content_agent(thread_id: str, task: str) -> Dict[str, Any]:
    agent = get_agent()
    # Important: use an invoke to completion for API
    result = await agent.ainvoke(
        {"messages": [("user", task)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    # Extract final assistant text if present
    final_text = ""
    platform = None
    slug = None

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["name"] == "write_file":
                    platform = tc["args"].get("platform")
                    slug = tc["args"].get("slug")

        if msg.type == "ai":
            final_text = msg.content

    files = {}
    if platform and slug:
        files = {
            "markdown": f"{platform}/{slug}/post.md",
            "hero_image": f"blogs/{slug}/hero.png",
            "social_image": f"{platform}/{slug}/image.png",
        }

    return {
        "final_text": final_text,
        "platform": platform,
        "slug": slug,
        "files": files,
    }