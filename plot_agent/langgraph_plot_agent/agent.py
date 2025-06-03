import os
from typing import Annotated, List

from agent_config import (
    PLOT_AGENT_INSTRUCTIONS,
    SQL_AGENT_INSTRUCTIONS,
)
from clickhouse_tools import execute_clickhouse_query
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from plot_tools import create_plot
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import agent
from typing_extensions import TypedDict

load_dotenv(".env")


Traceloop.init(app_name="langgraph")


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


tools_list = [execute_clickhouse_query, create_plot]

llm = ChatOpenAI(
    model=os.getenv("MODEL_ID"),
    api_key=os.getenv("LLM_GATEWAY_API_KEY"),
    base_url=os.getenv("LLM_GATEWAY_BASE_URL"),
    streaming=True,  # Enable streaming for the LLM
    temperature=0.0,
)

# Define combined instructions
COMBINED_AGENT_INSTRUCTIONS = (
    "You are an agent capable of generating Clickhouse SQL queries and creating visualizations from their results."
    "\n\nSQL QUERY GENERATION INSTRUCTIONS:\n"
    + "\n".join(SQL_AGENT_INSTRUCTIONS)
    + "\n\nDATA VISUALIZATION INSTRUCTIONS:\n"
    + "\n".join(PLOT_AGENT_INSTRUCTIONS)
)

# Define the custom prompt explicitly
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", COMBINED_AGENT_INSTRUCTIONS),  # explicit SQL instructions
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Create the agent using ReAct pattern with LangChain


@agent(name="sql_and_plot_workflow")
def create_sql_plot_agent(llm, tools_list, prompt):
    return create_react_agent(model=llm, tools=tools_list, prompt=prompt)


agent = create_sql_plot_agent(llm, tools_list, prompt)

# You can visualize the graph structure if running in a notebook environment
# try:
#     from IPython.display import Image, display
#     display(Image(agent.get_graph().draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

if __name__ == "__main__":
    # Test the agent with a sample query
    user_input = "List the top 5 most active users by request count in the last 30 days and plot the results."
    messages = [HumanMessage(content=user_input)]

    try:
        # Invoke the agent
        result = agent.invoke({"messages": messages})

        # Process and display the final result
        for message in result["messages"]:
            print(f"{message.type}: {message.content}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
