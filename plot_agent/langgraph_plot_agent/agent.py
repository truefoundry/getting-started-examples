from clickhouse_tools import execute_clickhouse_query
from plot_tools import create_plot
from typing import List, Dict, Any, Optional, Iterator
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

from langgraph.graph.message import AnyMessage, add_messages

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from langchain_openai import ChatOpenAI

from langgraph.prebuilt import ToolNode



from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# class SQLAndPlotWorkflow(Workflow):        
#     # SQL Agent that generates and executes Clickhouse queries
#     sql_agent: Agent = Agent(
#         model=OpenAIChat(id="openai-main/gpt-4o", api_key=os.getenv("LLM_GATEWAY_API_KEY"), base_url=os.getenv("LLM_GATEWAY_BASE_URL")),
#         description=SQL_AGENT_DESCRIPTION,
#         instructions=SQL_AGENT_INSTRUCTIONS,
#         tools=[ClickHouseTools()],
#         show_tool_calls=True,
#         markdown=True,
#         response_model=SQLQueryResult,
#         structured_outputs=True,
#         # debug_mode=True,
#     )

#     # Plot Agent that creates visualizations
#     plot_agent: Agent = Agent(
#         model=OpenAIChat(id="openai-main/gpt-4o", api_key=os.getenv("LLM_GATEWAY_API_KEY"), base_url=os.getenv("LLM_GATEWAY_BASE_URL")),
#         description=PLOT_AGENT_DESCRIPTION,
#         instructions=PLOT_AGENT_INSTRUCTIONS,
#         tools=[PlotTools()],
#         show_tool_calls=True,
#         markdown=True,
#         response_model=VisualizationRequest,
#         # structured_outputs=True,
#         # debug_mode=True,
#     )


#     def run_workflow(self, query: str) -> Iterator[RunResponse]:
#         """
#         Execute the SQL and plotting workflow.
        
#         Args:
#             query: Natural language query describing what to analyze
            
#         Yields:
#             RunResponse objects containing workflow progress and results
#         """
#         logger.info(f"Starting analysis for query: {query}")

#         # Step 1: Get SQL query results
#         sql_result = self._execute_sql_query(query)
#         if sql_result.error:
#             yield RunResponse(
#                 event="workflow_error",
#                 content=f"SQL Query Error: {sql_result.error}"
#             )
#             return
#         print(f"SQL Query Result: {sql_result.column_names}")
#         print(f"SQL Query Result: {sql_result.query}")
#         print(f"SQL Query Result: {sql_result.rows}")
#         # Step 2: Generate visualization
#         yield from self._create_visualization(sql_result)

#     def _execute_sql_query(self, query: str) -> SQLQueryResult:
#         """Execute SQL query and return results."""
#         MAX_ATTEMPTS = 3
        
#         for attempt in range(MAX_ATTEMPTS):
#             try:
#                 logger.info(f"Executing SQL query, attempt {attempt + 1}/{MAX_ATTEMPTS}")
#                 sql_response: RunResponse = self.sql_agent.run(query)
                
#                 if not sql_response or not sql_response.content:
#                     logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Empty SQL response")
#                     continue
                    
#                 if not isinstance(sql_response.content, SQLQueryResult):
#                     logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Invalid response type")
#                     continue
                
#                 return sql_response.content
                
#             except Exception as e:
#                 logger.warning(f"SQL query attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {str(e)}")
        
#         return SQLQueryResult(
#             query="",
#             column_names=[],
#             rows=[],
#             error=f"Failed to execute SQL query after {MAX_ATTEMPTS} attempts"
#         )

#     def _create_visualization(self, sql_result: SQLQueryResult) -> Iterator[RunResponse]:
#         """Create visualization from SQL results."""
#         try:
#             logger.info("Generating visualization request")
            
#             # Convert SQL result into tabular format that plot_tools expects
#             # Convert columns and rows into pipe-separated format
#             formatted_data = " | ".join(sql_result.column_names) + "\n"
#             formatted_data += "\n".join([" | ".join(row) for row in sql_result.rows])
            
#             # Get visualization request from plot agent
#             viz_response: RunResponse = self.plot_agent.run(
#                 json.dumps({
#                     "query": sql_result.query,
#                     "data": formatted_data
#                 }, indent=4)
#             )
            
#             if not viz_response or not viz_response.content:
#                 yield RunResponse(
#                     event="visualization_error",
#                     content="Empty visualization response"
#                 )
#                 return
                
#             # Find the PlotTools instance in the tools
#             plot_tools = None
#             for tool in self.plot_agent.tools:
#                 if isinstance(tool, PlotTools):
#                     plot_tools = tool
#                     break
                    
#             if not plot_tools:
#                 yield RunResponse(
#                     event="visualization_error",
#                     content="PlotTools not found in plot_agent tools"
#                 )
#                 return
            
#             # Handle both structured and unstructured responses
#             if isinstance(viz_response.content, VisualizationRequest):
#                 # Structured response case
#                 viz_request = viz_response.content
#                 logger.info(f"Using visualization request: {viz_request.model_dump()}")
#             else:
#                 # Don't handle unstructured responses, just return an error
#                 logger.error(f"Received unstructured response of type {type(viz_response.content)}")
#                 yield RunResponse(
#                     event="visualization_error",
#                     content=f"Visualization error: Expected VisualizationRequest but got {type(viz_response.content).__name__}"
#                 )
#                 return
            
#             # Now create the plot with proper error handling
#             logger.info(f"Creating {viz_request.plot_type} plot with x={viz_request.x_col}, y={viz_request.y_col}")
#             try:
#                 plot_result = plot_tools.create_plot(
#                     data=formatted_data,
#                     plot_type=viz_request.plot_type,
#                     x_col=viz_request.x_col,
#                     y_col=viz_request.y_col,
#                     title=viz_request.title,
#                     hue=viz_request.hue
#                 )
                
#                 yield RunResponse(
#                     event="visualization_complete",
#                     content=PlotResult(
#                         plot_type=viz_request.plot_type,
#                         plot_path=plot_result,
#                         x_col=viz_request.x_col,
#                         y_col=viz_request.y_col,
#                         title=viz_request.title
#                     )
#                 )
#                 return  # Add explicit return after successful completion
#             except Exception as plot_error:
#                 logger.error(f"Plot creation failed: {plot_error}")
#                 yield RunResponse(
#                     event="visualization_error",
#                     content=f"Failed to create plot: {plot_error}"
#                 )
#                 return
            
#         except Exception as e:
#             logger.error(f"Failed to create visualization: {str(e)}")
#             yield RunResponse(
#                 event="visualization_error",
#                 content=f"Failed to create visualization: {str(e)}"
#             )
#             return

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

tools_list = [execute_clickhouse_query, create_plot]

builder = StateGraph(State)

llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("LLM_GATEWAY_API_KEY"), base_url=os.getenv("LLM_GATEWAY_BASE_URL"))

llm.bind_tools(tools_list)

    # Define nodes: these do the work
builder.add_node("assistant", llm)
builder.add_node("tools", ToolNode(tools_list))


# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")

builder.add_edge("tools", "assistant")
builder.add_edge("assistant", "__end__")

agent = builder.compile()

from IPython.display import Image, display
display(Image(agent.get_graph().draw_mermaid_png()))



if __name__ == "__main__":
        