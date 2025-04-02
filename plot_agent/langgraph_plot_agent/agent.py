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
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv('.env')

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

tools_list = [execute_clickhouse_query, create_plot]

llm = ChatOpenAI(
    model=os.getenv("MODEL_ID"), 
    api_key=os.getenv("LLM_GATEWAY_API_KEY"), 
    base_url=os.getenv("LLM_GATEWAY_BASE_URL"),
    streaming=True,  # Enable streaming for the LLM
    temperature=0.0
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
prompt = ChatPromptTemplate.from_messages([
    ("system", COMBINED_AGENT_INSTRUCTIONS),  # explicit SQL instructions
    MessagesPlaceholder(variable_name="messages"),
])


agent = create_react_agent(
    model=llm,
    tools=tools_list,
    prompt=prompt
)

from IPython.display import Image, display

try:
    display(Image(agent.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass


if __name__ == "__main__":
    # Initialize with the user's message in the correct format
    user_input = "List the top 5 most active users by request count in the last 30 days and plot the results."
    messages = [HumanMessage(content=user_input)]
    
    try:
        # You should use the correct table name for costs
        # For debugging purposes, you might want to print available tables first
        result = agent.invoke({"messages": messages})
        
        # Process and display the final result
        for message in result["messages"]:
            print(f"{message.type}: {message.content}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")


result = agent.invoke({"messages": [HumanMessage(content="List top 5 models by usage count")]})

for message in result["messages"]:
    print(message.content)