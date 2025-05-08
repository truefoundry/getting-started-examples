from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.workflow import Workflow
from clickhouse_tools import ClickHouseTools
from plot_tools import PlotTools
from typing import List, Dict, Any, Optional, Iterator
from pydantic import BaseModel, Field
import json
import os
from agno.utils.log import logger
from dotenv import load_dotenv
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, agent, task

load_dotenv()

Traceloop.init(app_name="agno")

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

class SQLAndPlotWorkflow(Workflow):        
    # SQL Agent that generates and executes Clickhouse queries
    sql_agent: Agent = Agent(
        model=OpenAIChat(id="openai-main/gpt-4o", api_key=os.getenv("LLM_GATEWAY_API_KEY"), base_url=os.getenv("LLM_GATEWAY_BASE_URL")),
        description="You are an expert in generating and executing Clickhouse SQL queries from user queries in English.",
        instructions=[
            "First, generate an optimized and accurate ClickHouse SQL query based on the user's query. Make sure that only relevant fields are selected and queries are efficient.",
            "Then, always execute the generated SQL query against ClickHouse using a tool call.",
            "Return the SQL query in the format of a SQLQueryResult object.",
            "Please verify if you made the tool call to execute the sql query against clickhouse. If not retry go back to the previous step and make the tool call.",
            "We have a Clickhouse table called request_logs which contains the requests for the calls made to an LLM.",
            "The table structure is defined below in the format of columnName: type: description:",
            "- id: String: This is the row id which is a random string. Not very useful in queries.",
            "- model_id: String: The id of the model to which the LLM prompt was passed. Random string and not very useful in query generation.",
            "- model_name: String: The name of the model to which the LLM prompt was passed. The possible values are unknown.",
            "- request_type: String: This can be either chat, completion, embedding, or rerank. This is used to filter the logs for different model types.",
            "- tenant_name: String: Name of the tenant from which the request was made.",
            "- username: String: Email or name of the user who made the request.",
            "- prompt: String: The actual prompt that was passed to the LLM. This can be null if the user has decided not to log the prompt.",
            "- response: String: The response of the LLM - can be null if the user has decided not to log the response.",
            "- input_tokens: UInt64: Number of tokens in the input.",
            "- output_tokens: UInt64: Number of tokens in the output.",
            "- latency_in_ms: Float32: Time taken to get the response from the LLM in milliseconds.",
            "- cost: Float32: Cost of the request in USD.",
            "- error_code: UInt16: Error code in case the request errors out (e.g., 0, 404, 503, etc.).",
            "- error_detail: String: Additional details about the error.",
            "- metadata: Map(LowCardinality(String), String): Metadata associated with the request.",
            "- applied_configs: Map(LowCardinality(String), Map(LowCardinality(String), String)): Configuration settings applied to the request.",
            "- created_at: DateTime64(9) Delta(8), ZSTD(1): The timestamp when the request was made.",
            "Clickhouse has slighlty different syntax rules than MySQL or PostgreSQL. Please make sure to use the correct syntax for Clickhouse."
            "Syntax rule: Use toIntervalXXX(N) (e.g., toIntervalDay(30)) instead of INTERVAL N UNIT (e.g., INTERVAL 30 DAY) for interval arithmetic in ClickHouse."
            "Syntax rule: Do not end in a semicolon (;) in the query. Only end with a newline.",
        ],
        tools=[ClickHouseTools()],
        show_tool_calls=True,
        markdown=True,
        response_model=SQLQueryResult,
        structured_outputs=True,
        # debug_mode=True,
    )

    # Plot Agent that creates visualizations
    plot_agent: Agent = Agent(
        model=OpenAIChat(id="openai-main/gpt-4o", api_key=os.getenv("LLM_GATEWAY_API_KEY"), base_url=os.getenv("LLM_GATEWAY_BASE_URL")),
        description="You are an expert in creating data visualizations from SQL query results.",
        instructions=[
            "You will receive data from Clickhouse SQL queries in a tabular format with columns separated by ' | ' and rows separated by newlines.",
            "The data comes from a request_logs table with columns like: id, model_name, request_type, tenant_name, username, prompt, response, input_tokens, output_tokens, latency_in_ms, cost, error_code, error_detail, etc.",
            "Choose appropriate visualizations based on the data type and relationships to show:",
            "- Time series plots for metrics over time using created_at",
            "- Bar charts for categorical data like model_name, request_type, tenant_name",
            "- Histograms/distributions for numerical columns like tokens, latency, cost", 
            "- Scatter plots to show relationships between numerical metrics",
            "Ensure all visualizations have:",
            "- Clear titles describing the insight",
            "- Properly labeled axes with units where applicable",
            "- Legends for multiple series",
            "- Color schemes that are accessible",
            "Rules: ",
            "- The value of the x-axis should be a column name from the data.",
        ],
        tools=[PlotTools()],
        show_tool_calls=True,
        markdown=True,
        response_model=VisualizationRequest,
        # structured_outputs=True,
        # debug_mode=True,
    )


    @workflow(name="plotting workflow")
    def run_workflow(self, query: str) -> Iterator[RunResponse]:
        """
        Execute the SQL and plotting workflow.
        
        Args:
            query: Natural language query describing what to analyze
            
        Yields:
            RunResponse objects containing workflow progress and results
        """
        logger.info(f"Starting analysis for query: {query}")

        # Step 1: Get SQL query results
        sql_result = self._execute_sql_query(query)
        if sql_result.error:
            yield RunResponse(
                event="workflow_error",
                content=f"SQL Query Error: {sql_result.error}"
            )
            return
        print(f"SQL Query Result: {sql_result.column_names}")
        print(f"SQL Query Result: {sql_result.query}")
        print(f"SQL Query Result: {sql_result.rows}")
        # Step 2: Generate visualization
        yield from self._create_visualization(sql_result)

    @task(name="execute sql query")
    def _execute_sql_query(self, query: str) -> SQLQueryResult:
        """Execute SQL query and return results."""
        MAX_ATTEMPTS = 3
        
        for attempt in range(MAX_ATTEMPTS):
            try:
                logger.info(f"Executing SQL query, attempt {attempt + 1}/{MAX_ATTEMPTS}")
                sql_response: RunResponse = self.sql_agent.run(query)
                
                if not sql_response or not sql_response.content:
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Empty SQL response")
                    continue
                    
                if not isinstance(sql_response.content, SQLQueryResult):
                    logger.warning(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Invalid response type")
                    continue
                
                return sql_response.content
                
            except Exception as e:
                logger.warning(f"SQL query attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {str(e)}")
        
        return SQLQueryResult(
            query="",
            column_names=[],
            rows=[],
            error=f"Failed to execute SQL query after {MAX_ATTEMPTS} attempts"
        )

    @task(name="create visualization")
    def _create_visualization(self, sql_result: SQLQueryResult) -> Iterator[RunResponse]:
        """Create visualization from SQL results."""
        try:
            logger.info("Generating visualization request")
            
            # Convert SQL result into tabular format that plot_tools expects
            # Convert columns and rows into pipe-separated format
            formatted_data = " | ".join(sql_result.column_names) + "\n"
            formatted_data += "\n".join([" | ".join(row) for row in sql_result.rows])
            
            # Get visualization request from plot agent
            viz_response: RunResponse = self.plot_agent.run(
                json.dumps({
                    "query": sql_result.query,
                    "data": formatted_data
                }, indent=4)
            )
            
            if not viz_response or not viz_response.content:
                yield RunResponse(
                    event="visualization_error",
                    content="Empty visualization response"
                )
                return
                
            # Find the PlotTools instance in the tools
            plot_tools = None
            for tool in self.plot_agent.tools:
                if isinstance(tool, PlotTools):
                    plot_tools = tool
                    break
                    
            if not plot_tools:
                yield RunResponse(
                    event="visualization_error",
                    content="PlotTools not found in plot_agent tools"
                )
                return
            
            # Handle both structured and unstructured responses
            if isinstance(viz_response.content, VisualizationRequest):
                # Structured response case
                viz_request = viz_response.content
                logger.info(f"Using visualization request: {viz_request.model_dump()}")
            else:
                # Don't handle unstructured responses, just return an error
                logger.error(f"Received unstructured response of type {type(viz_response.content)}")
                yield RunResponse(
                    event="visualization_error",
                    content=f"Visualization error: Expected VisualizationRequest but got {type(viz_response.content).__name__}"
                )
                return
            
            # Now create the plot with proper error handling
            logger.info(f"Creating {viz_request.plot_type} plot with x={viz_request.x_col}, y={viz_request.y_col}")
            try:
                plot_result = plot_tools.create_plot(
                    data=formatted_data,
                    plot_type=viz_request.plot_type,
                    x_col=viz_request.x_col,
                    y_col=viz_request.y_col,
                    title=viz_request.title,
                    hue=viz_request.hue
                )
                
                yield RunResponse(
                    event="visualization_complete",
                    content=PlotResult(
                        plot_type=viz_request.plot_type,
                        plot_path=plot_result,
                        x_col=viz_request.x_col,
                        y_col=viz_request.y_col,
                        title=viz_request.title
                    )
                )
                return  # Add explicit return after successful completion
            except Exception as plot_error:
                logger.error(f"Plot creation failed: {plot_error}")
                yield RunResponse(
                    event="visualization_error",
                    content=f"Failed to create plot: {plot_error}"
                )
                return
            
        except Exception as e:
            logger.error(f"Failed to create visualization: {str(e)}")
            yield RunResponse(
                event="visualization_error",
                content=f"Failed to create visualization: {str(e)}"
            )
            return

if __name__ == "__main__":
    # Example usage:
    workflow = SQLAndPlotWorkflow()
    
    # Analyze and visualize data
    for response in workflow.run_workflow("Compare usage patterns across the top 5 models"):
        if response.event == "workflow_error":
            print(f"Error: {response.content}")
        elif response.event == "visualization_complete":
            plot_result = response.content
            print(f"Generated {plot_result.plot_type} plot at {plot_result.plot_path}")
