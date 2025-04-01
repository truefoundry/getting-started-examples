from clickhouse_tools import execute_clickhouse_query
from plot_tools import create_plot
from typing import List, Dict, Any, Union, Iterator
from models import SQLQueryResult, PlotResult, VisualizationRequest
from agent_config import (
    SQL_AGENT_DESCRIPTION,
    SQL_AGENT_INSTRUCTIONS,
    PLOT_AGENT_DESCRIPTION,
    PLOT_AGENT_INSTRUCTIONS
)
import json
import os
from langgraph.graph import StateGraph, START, END
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv('.env')

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

tools_list = [execute_clickhouse_query, create_plot]

def create_agent():
    builder = StateGraph(State)

    llm = ChatOpenAI(
        model=os.getenv("MODEL_ID"), 
        api_key=os.getenv("LLM_GATEWAY_API_KEY"), 
        base_url=os.getenv("LLM_GATEWAY_BASE_URL"),
        streaming=True  # Enable streaming for the LLM
    )

    llm.bind_tools(tools_list)

    # Define nodes: these do the work
    builder.add_node("assistant", llm)
    builder.add_node("tools", ToolNode(tools_list))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "assistant")
    builder.add_edge("tools", "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    builder.add_edge("assistant", "__end__")

    agent = builder.compile()
    return agent

agent = create_agent()

from IPython.display import Image, display

try:
    display(Image(agent.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

config = {"configurable": {"thread_id": "1"}}

user_input = "Show me the cost trends by model over the last week. Filter models that show a 0 cost."

if __name__ == "__main__":
    # Initialize with the user's message in the correct format
    messages = [HumanMessage(content=user_input)]
    
    # Stream the results with proper state initialization
    for step in agent.stream({"messages": messages}, config=config):
        # Get the state snapshot
        state_snapshot = step["messages"]
        
        # Process and display the latest message
        if len(state_snapshot) > 0:
            latest_message = state_snapshot[-1]
            
            # If it's an assistant or tool message, print it
            if isinstance(latest_message, (AIMessage, BaseMessage)):
                content = latest_message.content
                if isinstance(content, str):
                    print(f"{latest_message.type.upper()}: {content}")
                else:
                    print(f"{latest_message.type.upper()}: {json.dumps(content, indent=2)}")
        