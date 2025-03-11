from typing import List, Dict, Any, Optional, Iterator, TypedDict, Annotated, Literal, cast
from pydantic import BaseModel, Field
import json
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.pydantic_v1 import BaseModel as LCBaseModel
from langchain_core.pydantic_v1 import Field as LCField
from langchain_core.pydantic_v1 import validator
from langchain.agents.format_scratchpad import format_to_openai_tool_messages
from langchain.agents.output_parsers import OpenAIToolsAgentOutputParser
from langchain_core.runnables.config import RunnableConfig
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.callbacks.manager import CallbackManagerForChainRun
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import ToolMessage
from langchain_core.runnables import chain
from langchain_core.runnables.graph import Graph
from langchain.graphs import StateGraph
from langchain.graphs.graph import END
from clickhouse_tools import ClickHouseTools
from plot_tools import PlotTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# Define data models
class SQLQueryResult(BaseModel):
    query: str = Field(..., description="The SQL query that was executed.")
    column_names: List[str] = Field(..., description="List of column names in the query result.")
    rows: List[List[str]] = Field(..., description="List of row values, where each row is a list of column values.")
    error: Optional[str] = Field(None, description="Error message if the query failed.")

class PlotResult(BaseModel):
    plot_type: str = Field(..., description="Type of plot created.")
    plot_path: str = Field(..., description="Path to the saved plot image.")
    x_col: str = Field(..., description="Column used for x-axis.")
    y_col: Optional[str] = Field(None, description="Column used for y-axis.")
    title: Optional[str] = Field(None, description="Title of the plot.")
    error: Optional[str] = Field(None, description="Error message if plotting failed.")

class VisualizationRequest(BaseModel):
    plot_type: str = Field(..., description="Type of plot to create.")
    x_col: str = Field(..., description="Column for x-axis.")
    y_col: Optional[str] = Field(None, description="Column for y-axis.")
    title: Optional[str] = Field(None, description="Plot title.")
    hue: Optional[str] = Field(None, description="Column for color grouping.")

# Define state for the workflow
class WorkflowState(TypedDict):
    query: str
    sql_result: Optional[SQLQueryResult]
    viz_request: Optional[VisualizationRequest]
    plot_result: Optional[PlotResult]
    error: Optional[str]
    event: Optional[str]
    content: Optional[Any]

# Custom callback handler to track events
class EventTrackingHandler(BaseCallbackHandler):
    def __init__(self):
        self.events = []
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        self.events.append({"event": "chain_start", "content": serialized.get("name", "unknown")})
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        self.events.append({"event": "chain_end", "content": outputs})
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        self.events.append({"event": "tool_start", "content": f"{serialized.get('name', 'unknown')}: {input_str}"})
        
    def on_tool_end(self, output: str, **kwargs) -> None:
        self.events.append({"event": "tool_end", "content": output})
        
    def on_chain_error(self, error: Exception, **kwargs) -> None:
        self.events.append({"event": "chain_error", "content": str(error)})
        
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        self.events.append({"event": "tool_error", "content": str(error)})

# Create the SQL Agent
def create_sql_agent():
    # Initialize the ClickHouse tools
    clickhouse_tools = ClickHouseTools()
    
    # Define the system prompt for the SQL agent
    sql_system_prompt = """You are an expert in generating and executing Clickhouse SQL queries from user queries in English.
First, generate an optimized and accurate ClickHouse SQL query based on the user's query. Make sure that only relevant fields are selected and queries are efficient.
Then, always execute the generated SQL query against ClickHouse using a tool call.
Return the SQL query in the format of a SQLQueryResult object.

We have a Clickhouse table called request_logs which contains the requests for the calls made to an LLM.
The table structure is defined below in the format of columnName: type: description:
- id: String: This is the row id which is a random string. Not very useful in queries.
- model_id: String: The id of the model to which the LLM prompt was passed. Random string and not very useful in query generation.
- model_name: String: The name of the model to which the LLM prompt was passed. The possible values are unknown.
- request_type: String: This can be either chat, completion, embedding, or rerank. This is used to filter the logs for different model types.
- tenant_name: String: Name of the tenant from which the request was made.
- username: String: Email or name of the user who made the request.
- prompt: String: The actual prompt that was passed to the LLM. This can be null if the user has decided not to log the prompt.
- response: String: The response of the LLM - can be null if the user has decided not to log the response.
- input_tokens: UInt64: Number of tokens in the input.
- output_tokens: UInt64: Number of tokens in the output.
- latency_in_ms: Float32: Time taken to get the response from the LLM in milliseconds.
- cost: Float32: Cost of the request in USD.
- error_code: UInt16: Error code in case the request errors out (e.g., 0, 404, 503, etc.).
- error_detail: String: Additional details about the error.
- metadata: Map(LowCardinality(String), String): Metadata associated with the request.
- applied_configs: Map(LowCardinality(String), Map(LowCardinality(String), String)): Configuration settings applied to the request.
- created_at: DateTime64(9) Delta(8), ZSTD(1): The timestamp when the request was made.
"""
    
    # Create the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Create the tools
    tools = [
        clickhouse_tools.execute_query_tool
    ]
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", sql_system_prompt),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}")
    ])
    
    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
    
    # Create a parser for the SQLQueryResult
    sql_parser = PydanticOutputParser(pydantic_object=SQLQueryResult)
    
    # Define a function to process the agent output into a SQLQueryResult
    def process_sql_output(output):
        try:
            # Check if output is already a SQLQueryResult
            if isinstance(output, dict) and "query" in output and "column_names" in output and "rows" in output:
                return SQLQueryResult(**output)
            
            # Try to extract the SQL query result from the agent output
            if isinstance(output, dict) and "output" in output:
                content = output["output"]
                
                # If it's a string, try to parse it as JSON
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        return SQLQueryResult(**data)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, try to extract the query and result from the text
                        # This is a fallback for when the agent doesn't return a properly structured output
                        query = ""
                        column_names = []
                        rows = []
                        error = None
                        
                        # Look for the query in the output
                        if "query" in content.lower():
                            query_start = content.lower().find("query")
                            query_end = content.find("\n", query_start)
                            if query_end == -1:
                                query_end = len(content)
                            query = content[query_start + 6:query_end].strip()
                        
                        # Look for column names and rows in the output
                        if "|" in content:
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if "|" in line:
                                    column_names = [col.strip() for col in line.split("|") if col.strip()]
                                    for row_line in lines[i+1:]:
                                        if "|" in row_line:
                                            rows.append([cell.strip() for cell in row_line.split("|") if cell.strip()])
                                    break
                        
                        return SQLQueryResult(
                            query=query,
                            column_names=column_names,
                            rows=rows,
                            error=error
                        )
                
                # If it's a dict, try to extract the SQLQueryResult fields
                if isinstance(content, dict):
                    return SQLQueryResult(
                        query=content.get("query", ""),
                        column_names=content.get("column_names", []),
                        rows=content.get("rows", []),
                        error=content.get("error")
                    )
            
            # If we get here, we couldn't parse the output
            return SQLQueryResult(
                query="",
                column_names=[],
                rows=[],
                error=f"Failed to parse SQL query result: {output}"
            )
        except Exception as e:
            logger.error(f"Error processing SQL output: {e}")
            return SQLQueryResult(
                query="",
                column_names=[],
                rows=[],
                error=f"Error processing SQL output: {e}"
            )
    
    # Create the chain
    sql_chain = agent_executor | RunnableLambda(process_sql_output)
    
    return sql_chain

# Create the Plot Agent
def create_plot_agent():
    # Initialize the Plot tools
    plot_tools = PlotTools()
    
    # Define the system prompt for the Plot agent
    plot_system_prompt = """You are an expert in creating data visualizations from SQL query results.
You will receive data from Clickhouse SQL queries in a tabular format with columns separated by ' | ' and rows separated by newlines.
The data comes from a request_logs table with columns like: id, model_name, request_type, tenant_name, username, prompt, response, input_tokens, output_tokens, latency_in_ms, cost, error_code, error_detail, etc.

Choose appropriate visualizations based on the data type and relationships to show:
- Time series plots for metrics over time using created_at
- Bar charts for categorical data like model_name, request_type, tenant_name
- Histograms/distributions for numerical columns like tokens, latency, cost
- Scatter plots to show relationships between numerical metrics

Ensure all visualizations have:
- Clear titles describing the insight
- Properly labeled axes with units where applicable
- Legends for multiple series
- Color schemes that are accessible

Provide a brief analysis of key patterns, trends, or anomalies observed in each visualization.
"""
    
    # Create the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Create the tools
    tools = [
        plot_tools.create_plot_tool
    ]
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", plot_system_prompt),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}")
    ])
    
    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
    
    # Create a parser for the VisualizationRequest
    viz_parser = PydanticOutputParser(pydantic_object=VisualizationRequest)
    
    # Define a function to process the agent output into a VisualizationRequest
    def process_plot_output(output):
        try:
            # Check if output is already a VisualizationRequest
            if isinstance(output, dict) and "plot_type" in output and "x_col" in output:
                return VisualizationRequest(**output)
            
            # Try to extract the visualization request from the agent output
            if isinstance(output, dict) and "output" in output:
                content = output["output"]
                
                # If it's a string, try to parse it as JSON
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        return VisualizationRequest(**data)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, try to extract the visualization request from the text
                        # This is a fallback for when the agent doesn't return a properly structured output
                        plot_type = "bar"  # Default
                        x_col = ""
                        y_col = None
                        title = None
                        hue = None
                        
                        # Look for common plot types in the output
                        for pt in ["line", "bar", "scatter", "histogram", "box", "violin"]:
                            if pt in content.lower():
                                plot_type = pt
                                break
                        
                        # Look for column names in the output
                        if "x_col" in content.lower() or "x-axis" in content.lower():
                            x_start = max(content.lower().find("x_col"), content.lower().find("x-axis"))
                            x_end = content.find("\n", x_start)
                            if x_end == -1:
                                x_end = len(content)
                            x_col_text = content[x_start:x_end]
                            # Extract the column name after the colon or equals sign
                            if ":" in x_col_text:
                                x_col = x_col_text.split(":", 1)[1].strip()
                            elif "=" in x_col_text:
                                x_col = x_col_text.split("=", 1)[1].strip()
                        
                        # Look for y column in the output
                        if "y_col" in content.lower() or "y-axis" in content.lower():
                            y_start = max(content.lower().find("y_col"), content.lower().find("y-axis"))
                            y_end = content.find("\n", y_start)
                            if y_end == -1:
                                y_end = len(content)
                            y_col_text = content[y_start:y_end]
                            # Extract the column name after the colon or equals sign
                            if ":" in y_col_text:
                                y_col = y_col_text.split(":", 1)[1].strip()
                            elif "=" in y_col_text:
                                y_col = y_col_text.split("=", 1)[1].strip()
                        
                        # Look for title in the output
                        if "title" in content.lower():
                            title_start = content.lower().find("title")
                            title_end = content.find("\n", title_start)
                            if title_end == -1:
                                title_end = len(content)
                            title_text = content[title_start:title_end]
                            # Extract the title after the colon or equals sign
                            if ":" in title_text:
                                title = title_text.split(":", 1)[1].strip()
                            elif "=" in title_text:
                                title = title_text.split("=", 1)[1].strip()
                        
                        return VisualizationRequest(
                            plot_type=plot_type,
                            x_col=x_col or "Unknown",
                            y_col=y_col,
                            title=title,
                            hue=hue
                        )
                
                # If it's a dict, try to extract the VisualizationRequest fields
                if isinstance(content, dict):
                    return VisualizationRequest(
                        plot_type=content.get("plot_type", "bar"),
                        x_col=content.get("x_col", "Unknown"),
                        y_col=content.get("y_col"),
                        title=content.get("title"),
                        hue=content.get("hue")
                    )
            
            # If we get here, we couldn't parse the output
            return VisualizationRequest(
                plot_type="bar",
                x_col="Unknown",
                y_col=None,
                title=None,
                hue=None
            )
        except Exception as e:
            logger.error(f"Error processing plot output: {e}")
            return VisualizationRequest(
                plot_type="bar",
                x_col="Unknown",
                y_col=None,
                title=None,
                hue=None
            )
    
    # Create the chain
    plot_chain = agent_executor | RunnableLambda(process_plot_output)
    
    return plot_chain

# Create the workflow
class SQLAndPlotWorkflow:
    def __init__(self):
        self.sql_agent = create_sql_agent()
        self.plot_agent = create_plot_agent()
        self.plot_tools = PlotTools()
        
    def run_workflow(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Execute the SQL and plotting workflow.
        
        Args:
            query: Natural language query describing what to analyze
            
        Yields:
            Dict objects containing workflow progress and results
        """
        logger.info(f"Starting analysis for query: {query}")
        
        # Step 1: Get SQL query results
        try:
            sql_result = self._execute_sql_query(query)
            if sql_result.error:
                yield {
                    "event": "workflow_error",
                    "content": f"SQL Query Error: {sql_result.error}"
                }
                return
            
            logger.info(f"SQL Query Result: {sql_result.column_names}")
            logger.info(f"SQL Query Result: {sql_result.query}")
            logger.info(f"SQL Query Result: {len(sql_result.rows)} rows")
            
            # Step 2: Generate visualization
            yield from self._create_visualization(sql_result)
            
        except Exception as e:
            logger.error(f"Error in workflow: {e}")
            yield {
                "event": "workflow_error",
                "content": f"Workflow Error: {str(e)}"
            }
    
    def _execute_sql_query(self, query: str) -> SQLQueryResult:
        """Execute SQL query and return results."""
        MAX_ATTEMPTS = 3
        
        for attempt in range(MAX_ATTEMPTS):
            try:
                logger.info(f"Executing SQL query, attempt {attempt + 1}/{MAX_ATTEMPTS}")
                sql_response = self.sql_agent.invoke({"input": query})
                
                if not sql_response:
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Empty SQL response")
                    continue
                
                if isinstance(sql_response, SQLQueryResult):
                    return sql_response
                
                # If we get here, we couldn't parse the output
                logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Invalid response type: {type(sql_response)}")
                
            except Exception as e:
                logger.warning(f"SQL query attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {str(e)}")
        
        return SQLQueryResult(
            query="",
            column_names=[],
            rows=[],
            error=f"Failed to execute SQL query after {MAX_ATTEMPTS} attempts"
        )
    
    def _create_visualization(self, sql_result: SQLQueryResult) -> Iterator[Dict[str, Any]]:
        """Create visualization from SQL results."""
        try:
            logger.info("Generating visualization request")
            
            # Convert SQL result into tabular format that plot_tools expects
            # Convert columns and rows into pipe-separated format
            formatted_data = " | ".join(sql_result.column_names) + "\n"
            formatted_data += "\n".join([" | ".join(row) for row in sql_result.rows])
            
            # Get visualization request from plot agent
            viz_input = json.dumps({
                "query": sql_result.query,
                "data": formatted_data
            }, indent=4)
            
            viz_response = self.plot_agent.invoke({"input": viz_input})
            
            if not viz_response:
                yield {
                    "event": "visualization_error",
                    "content": "Empty visualization response"
                }
                return
            
            # Handle the visualization request
            if isinstance(viz_response, VisualizationRequest):
                viz_request = viz_response
                logger.info(f"Using visualization request: {viz_request.model_dump()}")
            else:
                # Try to convert to VisualizationRequest
                try:
                    viz_request = VisualizationRequest(
                        plot_type=viz_response.get("plot_type", "bar"),
                        x_col=viz_response.get("x_col", "Unknown"),
                        y_col=viz_response.get("y_col"),
                        title=viz_response.get("title"),
                        hue=viz_response.get("hue")
                    )
                except Exception as e:
                    logger.error(f"Failed to parse visualization request: {e}")
                    yield {
                        "event": "visualization_error",
                        "content": f"Failed to parse visualization request: {e}"
                    }
                    return
            
            # Now create the plot with proper error handling
            logger.info(f"Creating {viz_request.plot_type} plot with x={viz_request.x_col}, y={viz_request.y_col}")
            try:
                plot_result = self.plot_tools.create_plot(
                    data=formatted_data,
                    plot_type=viz_request.plot_type,
                    x_col=viz_request.x_col,
                    y_col=viz_request.y_col,
                    title=viz_request.title,
                    hue=viz_request.hue
                )
                
                yield {
                    "event": "visualization_complete",
                    "content": PlotResult(
                        plot_type=viz_request.plot_type,
                        plot_path=plot_result,
                        x_col=viz_request.x_col,
                        y_col=viz_request.y_col,
                        title=viz_request.title
                    )
                }
                
            except Exception as e:
                logger.error(f"Error creating plot: {e}")
                yield {
                    "event": "visualization_error",
                    "content": f"Error creating plot: {e}"
                }
                
        except Exception as e:
            logger.error(f"Error in visualization process: {e}")
            yield {
                "event": "visualization_error",
                "content": f"Error in visualization process: {e}"
            }

# For testing
if __name__ == "__main__":
    workflow = SQLAndPlotWorkflow()
    query = "Show me the cost trends by model over the last week"
    
    for response in workflow.run_workflow(query):
        print(f"Event: {response['event']}")
        print(f"Content: {response['content']}")
