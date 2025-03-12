from typing import List, Dict, Any, Optional, Iterator, TypedDict, Literal
from pydantic import BaseModel, Field
import json
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from clickhouse_tools import ClickHouseTools
from plot_tools import PlotTools

from dotenv import load_dotenv

load_dotenv()

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
    messages: List[Dict[str, Any]]
    next: Optional[str]

# Custom callback handler to track events
class EventTrackingHandler:
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

# Initialize tools
clickhouse_tools = ClickHouseTools()
plot_tools = PlotTools()

# Define the SQL system prompt
SQL_SYSTEM_PROMPT = """You are an expert in generating and executing Clickhouse SQL queries from user queries in English.
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

# Define the Plot system prompt
PLOT_SYSTEM_PROMPT = """You are an expert in creating data visualizations from SQL query results.
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

# Define the nodes for the graph
def initialize_state(query: str) -> WorkflowState:
    """Initialize the workflow state with the user query."""
    return WorkflowState(
        query=query,
        sql_result=None,
        viz_request=None,
        plot_result=None,
        error=None,
        messages=[{"role": "user", "content": query}],
        next=None
    )

def sql_agent(state: WorkflowState) -> WorkflowState:
    """Execute SQL query based on the user query."""
    try:
        # Create the SQL agent with tools
        tools = [clickhouse_tools.execute_query_tool]
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SQL_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the chain
        chain = prompt | llm.bind_tools(tools)
        
        # Execute the chain
        response = chain.invoke({"messages": state["messages"]})
        
        # Process the response
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_call = response.tool_calls[0]
            if tool_call.name == "execute_query":
                query = tool_call.args.get("query", "")
                result = clickhouse_tools.execute_query(query)
                
                # Create SQLQueryResult
                sql_result = SQLQueryResult(
                    query=result["query"],
                    column_names=result["column_names"],
                    rows=result["rows"],
                    error=result["error"]
                )
                
                # Update state
                state["sql_result"] = sql_result
                state["messages"].append({"role": "assistant", "content": f"I've executed the SQL query: {query}"})
                state["messages"].append({"role": "function", "name": "execute_query", "content": json.dumps(result)})
                
                if sql_result.error:
                    state["error"] = f"SQL Query Error: {sql_result.error}"
                    state["next"] = "end"
                else:
                    state["next"] = "plot_agent"
            else:
                state["error"] = f"Unexpected tool call: {tool_call.name}"
                state["next"] = "end"
        else:
            # No tool call, just a message
            state["messages"].append({"role": "assistant", "content": response.content})
            state["error"] = "SQL agent did not execute a query"
            state["next"] = "end"
    except Exception as e:
        logger.error(f"Error in SQL agent: {e}")
        state["error"] = f"SQL Agent Error: {str(e)}"
        state["next"] = "end"
    
    return state

def plot_agent(state: WorkflowState) -> WorkflowState:
    """Generate visualization request based on SQL results."""
    try:
        # Check if we have SQL results
        if not state["sql_result"]:
            state["error"] = "No SQL results available for visualization"
            state["next"] = "end"
            return state
        
        sql_result = state["sql_result"]
        
        # Convert SQL result into tabular format
        formatted_data = " | ".join(sql_result.column_names) + "\n"
        formatted_data += "\n".join([" | ".join(row) for row in sql_result.rows])
        
        # Create the plot agent with tools
        tools = [plot_tools.create_plot_tool]
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", PLOT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Add SQL result to messages
        viz_input = {
            "role": "user", 
            "content": f"Based on the SQL query: {sql_result.query}\n\nHere is the data:\n{formatted_data}\n\nWhat visualization would be most appropriate for this data?"
        }
        state["messages"].append(viz_input)
        
        # Create the chain
        chain = prompt | llm.bind_tools(tools)
        
        # Execute the chain
        response = chain.invoke({"messages": state["messages"]})
        
        # Process the response
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_call = response.tool_calls[0]
            if tool_call.name == "create_plot":
                args = tool_call.args
                
                # Create VisualizationRequest
                viz_request = VisualizationRequest(
                    plot_type=args.get("plot_type", "bar"),
                    x_col=args.get("x_col", ""),
                    y_col=args.get("y_col"),
                    title=args.get("title"),
                    hue=args.get("hue")
                )
                
                # Update state
                state["viz_request"] = viz_request
                state["messages"].append({"role": "assistant", "content": f"I'll create a {viz_request.plot_type} plot with x={viz_request.x_col}, y={viz_request.y_col}"})
                
                # Create the plot
                plot_path = plot_tools.create_plot(
                    data=formatted_data,
                    plot_type=viz_request.plot_type,
                    x_col=viz_request.x_col,
                    y_col=viz_request.y_col,
                    title=viz_request.title,
                    hue=viz_request.hue
                )
                
                # Create PlotResult
                plot_result = PlotResult(
                    plot_type=viz_request.plot_type,
                    plot_path=plot_path,
                    x_col=viz_request.x_col,
                    y_col=viz_request.y_col,
                    title=viz_request.title
                )
                
                # Update state
                state["plot_result"] = plot_result
                state["messages"].append({"role": "function", "name": "create_plot", "content": json.dumps(plot_result.dict())})
                state["next"] = "end"
            else:
                state["error"] = f"Unexpected tool call: {tool_call.name}"
                state["next"] = "end"
        else:
            # No tool call, just a message
            state["messages"].append({"role": "assistant", "content": response.content})
            state["error"] = "Plot agent did not create a visualization"
            state["next"] = "end"
    except Exception as e:
        logger.error(f"Error in plot agent: {e}")
        state["error"] = f"Plot Agent Error: {str(e)}"
        state["next"] = "end"
    
    return state

def should_end(state: WorkflowState) -> Literal["sql_agent", "plot_agent", "end"]:
    """Determine the next node in the graph."""
    if state["error"]:
        return "end"
    
    if state["next"]:
        return state["next"]
    
    if not state["sql_result"]:
        return "sql_agent"
    
    if not state["plot_result"]:
        return "plot_agent"
    
    return "end"

# Create the graph
def create_workflow_graph():
    """Create the workflow graph using LangGraph."""
    # Define the nodes
    workflow = StateGraph(WorkflowState)
    
    # Add the nodes
    workflow.add_node("sql_agent", sql_agent)
    workflow.add_node("plot_agent", plot_agent)
    
    # Add the edges
    workflow.add_conditional_edges(
        "sql_agent",
        should_end,
        {
            "sql_agent": "sql_agent",
            "plot_agent": "plot_agent",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "plot_agent",
        should_end,
        {
            "sql_agent": "sql_agent",
            "plot_agent": "plot_agent",
            "end": END
        }
    )
    
    # Set the entry point
    workflow.set_entry_point("sql_agent")
    
    return workflow.compile()

# Create the workflow
class SQLAndPlotWorkflow:
    def __init__(self):
        self.graph = create_workflow_graph()
        
    def run_workflow(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Execute the SQL and plotting workflow.
        
        Args:
            query: Natural language query describing what to analyze
            
        Yields:
            Dict objects containing workflow progress and results
        """
        logger.info(f"Starting analysis for query: {query}")
        
        # Initialize the state
        state = initialize_state(query)
        
        # Run the graph
        for step in self.graph.stream(state):
            current_state = step.values
            
            # Yield progress updates
            if current_state.get("error"):
                yield {
                    "event": "workflow_error",
                    "content": current_state["error"]
                }
            
            if current_state.get("sql_result") and not current_state.get("plot_result"):
                yield {
                    "event": "sql_complete",
                    "content": current_state["sql_result"]
                }
            
            if current_state.get("plot_result"):
                yield {
                    "event": "visualization_complete",
                    "content": current_state["plot_result"]
                }
        
        # Yield final result
        final_state = step.values
        if final_state.get("plot_result"):
            yield {
                "event": "workflow_complete",
                "content": {
                    "sql_result": final_state["sql_result"],
                    "plot_result": final_state["plot_result"]
                }
            }
        elif final_state.get("sql_result"):
            yield {
                "event": "workflow_complete",
                "content": {
                    "sql_result": final_state["sql_result"]
                }
            }
        else:
            yield {
                "event": "workflow_error",
                "content": final_state.get("error", "Unknown error")
            }

# Function to visualize the graph
def plot_graph():
    """Generate a visualization of the workflow graph."""
    import graphviz
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add the nodes
    workflow.add_node("sql_agent", sql_agent)
    workflow.add_node("plot_agent", plot_agent)
    
    # Add the edges
    workflow.add_conditional_edges(
        "sql_agent",
        should_end,
        {
            "sql_agent": "sql_agent",
            "plot_agent": "plot_agent",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "plot_agent",
        should_end,
        {
            "sql_agent": "sql_agent",
            "plot_agent": "plot_agent",
            "end": END
        }
    )
    
    # Set the entry point
    workflow.set_entry_point("sql_agent")
    
    # Generate the graph visualization
    dot = graphviz.Digraph()
    
    # Add nodes
    dot.node("start", "Start", shape="ellipse")
    dot.node("sql_agent", "SQL Agent", shape="box")
    dot.node("plot_agent", "Plot Agent", shape="box")
    dot.node("end", "End", shape="ellipse")
    
    # Add edges
    dot.edge("start", "sql_agent")
    dot.edge("sql_agent", "sql_agent", label="retry")
    dot.edge("sql_agent", "plot_agent", label="success")
    dot.edge("sql_agent", "end", label="error")
    dot.edge("plot_agent", "plot_agent", label="retry")
    dot.edge("plot_agent", "sql_agent", label="need more data")
    dot.edge("plot_agent", "end", label="complete/error")
    
    # Save the graph
    graph_path = os.path.join(PLOTS_DIR, "workflow_graph.png")
    dot.render(os.path.splitext(graph_path)[0], format="png", cleanup=True)
    
    return graph_path

# For testing
if __name__ == "__main__":
    workflow = SQLAndPlotWorkflow()
    query = "Show me the cost trends by model over the last week"
    
    for response in workflow.run_workflow(query):
        print(f"Event: {response['event']}")
        print(f"Content: {response['content']}")
    
    # Generate and display the graph visualization
    graph_path = plot_graph()
    print(f"Graph visualization saved to: {graph_path}")
