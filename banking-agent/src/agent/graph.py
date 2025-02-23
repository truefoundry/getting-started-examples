from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from src.agent.banking_tools import tools
from src.agent.llm import llm
from src.agent.prompt import prompt_template

memory = MemorySaver()

AGENT = create_react_agent(model=llm, tools=tools, state_modifier=prompt_template, checkpointer=memory)


async def get_ai_response(events):
    for event in reversed(events):
        if event.get("messages"):
            last_message = event["messages"][-1]
            if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                try:
                    content = last_message.content
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        return " ".join([str(item) for sublist in content for item in sublist])
                    elif isinstance(content, dict):
                        return " ".join([str(v) for k, v in content.items() if isinstance(v, str)])
                    else:
                        return str(content)
                except Exception as e:
                    # Log the exception
                    print(f"Error: {e}")
                    return "An error occurred while processing the response."

    return None


def print_event(event):
    message = event.get("messages", [])
    if message:
        if isinstance(message, list):
            message = message[-1]
        message.pretty_print()


async def run_agent(thread_id: str, user_input: str):
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", user_input)]}

    events = []
    async for event in AGENT.astream(inputs, config=config, stream_mode="values"):
        print_event(event)
        events.append(event)

    response = await get_ai_response(events)
    if response is None:
        response = "An internal error has occurred."
    return {"response": response}
