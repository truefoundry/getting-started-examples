from typing import List, Dict, Any, Optional, Iterator, TypedDict, Literal, Union, Annotated, Tuple
from pydantic import BaseModel, Field
import json
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from langgraph.graph.message import add_messages
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
class AgentState(TypedDict):
    """State for the React agent workflow."""
    query: str
    sql_result: Optional[SQLQueryResult]
    plot_result: Optional[PlotResult]
    error: Optional[str]
    messages: Annotated[List[Dict[str, Any]], add_messages]

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

# Define the system prompt for the React agent
REACT_SYSTEM_PROMPT = """You are an expert data analyst that can generate SQL queries and create visualizations.

You have access to a Clickhouse database with a table called request_logs which contains the requests for the calls made to an LLM.
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

You have access to two tools:
1. execute_query: Use this to run SQL queries against the Clickhouse database
2. create_plot: Use this to create visualizations from the SQL query results

Your task is to:
1. Understand the user's request for data analysis
2. Generate and execute an appropriate SQL query to get the data
3. Create a suitable visualization based on the query results
4. Provide insights about the data

For visualizations, choose appropriate types based on the data:
- Time series plots for metrics over time using created_at
- Bar charts for categorical data like model_name, request_type, tenant_name
- Histograms/distributions for numerical columns like tokens, latency, cost
- Scatter plots to show relationships between numerical metrics

Ensure all visualizations have:
- Clear titles describing the insight
- Properly labeled axes with units where applicable
- Legends for multiple series
- Color schemes that are accessible

Follow these steps:
1. First, generate and execute a SQL query to get the data needed
2. Then, create a visualization from the query results
3. Finally, provide insights about what the data shows

Always think step by step and use the tools in the correct order.
"""

# Create the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Define the tools for the agent
def get_tools():
    """Get the tools for the agent."""
    return [
        clickhouse_tools.execute_query_tool,
        plot_tools.create_plot_tool
    ]

# Initialize the state
def initialize_state(query: str) -> AgentState:
    """Initialize the agent state with the user query."""
    return AgentState(
        query=query,
        sql_result=None,
        plot_result=None,
        error=None,
        messages=[{"role": "user", "content": query}],
        intermediate_steps=[]
    )

# Define the React agent
def react_agent(state: AgentState) -> Dict[str, Any]:
    """React agent that can use both SQL and plot tools."""
    # Get the tools
    tools = get_tools()
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", REACT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Format intermediate steps for the agent scratchpad
    def format_intermediate_steps(intermediate_steps):
        thoughts = []
        for action, observation in intermediate_steps:
            thoughts.append({
                "role": "assistant",
                "content": f"Action: {action.tool}\nAction Input: {json.dumps(action.tool_input)}"
            })
            thoughts.append({
                "role": "function",
                "name": action.tool,
                "content": str(observation)
            })
        return thoughts
    
    # Create the chain
    chain = prompt | llm.bind_tools(tools)
    
    # Prepare the input
    input_dict = {
        "messages": state["messages"],
        "agent_scratchpad": format_intermediate_steps(state["intermediate_steps"])
    }
    
    # Execute the chain
    response = chain.invoke(input_dict)
    
    # Check if the agent wants to use a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]
        return {
            "tool": tool_call.name,
            "tool_input": tool_call.args,
            "messages": state["messages"]
        }
    
    # If no tool calls, the agent is done
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": response.content}],
        "tool": None
    }

# Create the tool executor node
def tool_executor(state: AgentState, tool_invocation: Dict[str, Any]) -> AgentState:
    """Execute a tool and update the state."""
    # Extract tool information
    tool_name = tool_invocation["tool"]
    tool_input = tool_invocation["tool_input"]
    
    # If no tool is specified, return the state as is
    if tool_name is None:
        return state
    
    # Create a tool invocation object
    invocation = ToolInvocation(
        tool=tool_name,
        tool_input=tool_input
    )
    
    # Create a tool executor
    tools = get_tools()
    executor = ToolExecutor(tools)
    
    # Execute the tool
    try:
        result = executor.invoke(invocation)
        
        # Update the state based on the tool used
        if tool_name == "execute_query":
            # Parse the result
            try:
                query_result = json.loads(result)
                sql_result = SQLQueryResult(
                    query=query_result["query"],
                    column_names=query_result["column_names"],
                    rows=query_result["rows"],
                    error=query_result["error"]
                )
                state["sql_result"] = sql_result
                
                # Format the data for the next step
                if not sql_result.error and sql_result.rows:
                    # Add a message to help the agent understand the data
                    formatted_data = " | ".join(sql_result.column_names) + "\n"
                    formatted_data += "\n".join([" | ".join(row) for row in sql_result.rows[:10]])  # Show first 10 rows
                    
                    data_message = {
                        "role": "user", 
                        "content": f"Here are the results of your SQL query: {sql_result.query}\n\n{formatted_data}\n\nPlease create an appropriate visualization for this data."
                    }
                    state["messages"].append(data_message)
                
            except Exception as e:
                logger.error(f"Error parsing SQL result: {e}")
                state["error"] = f"Error parsing SQL result: {str(e)}"
        
        elif tool_name == "create_plot":
            # Parse the result
            try:
                plot_result_dict = json.loads(result)
                plot_result = PlotResult(
                    plot_type=plot_result_dict["plot_type"],
                    plot_path=plot_result_dict["plot_path"],
                    x_col=plot_result_dict["x_col"],
                    y_col=plot_result_dict["y_col"],
                    title=plot_result_dict["title"],
                    error=plot_result_dict.get("error")
                )
                state["plot_result"] = plot_result
                
                # Add a message to help the agent provide insights
                if not plot_result.error:
                    insight_message = {
                        "role": "user", 
                        "content": f"You've created a {plot_result.plot_type} plot with x={plot_result.x_col}, y={plot_result.y_col}. Please provide insights about what this visualization shows."
                    }
                    state["messages"].append(insight_message)
                
            except Exception as e:
                logger.error(f"Error parsing plot result: {e}")
                state["error"] = f"Error parsing plot result: {str(e)}"
        
        # Add the tool invocation and result to intermediate steps
        state["intermediate_steps"].append((invocation, result))
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        state["error"] = f"Error executing tool {tool_name}: {str(e)}"
    
    return state

# Create the graph
def create_workflow_graph():
    """Create the workflow graph using LangGraph."""
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add the nodes
    workflow.add_node("agent", react_agent)
    workflow.add_node("action", tool_executor)
    
    # Add the edges
    workflow.add_edge("agent", "action")
    workflow.add_edge("action", "agent")
    
    # Add conditional edges
    def should_continue(state: AgentState) -> Literal["agent", "end"]:
        """Determine if the agent should continue or end."""
        # Check if there's an error
        if state["error"]:
            return "end"
        
        # Check if the agent is done
        if len(state["intermediate_steps"]) > 0:
            # Check if the last output was a tool call
            last_action = state["intermediate_steps"][-1][0]
            
            # If we've created a plot and provided insights, we're done
            if last_action.tool == "create_plot" and state["plot_result"]:
                # Check if we have at least one more message after the plot
                if len(state["messages"]) > 0 and state["messages"][-1].get("role") == "assistant":
                    return "end"
        
        # Check if the last agent output didn't request a tool
        last_output = state.get("tool")
        if last_output is None:
            return "end"
        
        # Continue the agent
        return "agent"
    
    # Add conditional edge from action to either agent or end
    workflow.add_conditional_edges("action", should_continue, {
        "agent": "agent",
        "end": END
    })
    
    # Set the entry point
    workflow.set_entry_point("agent")
    
    return workflow.compile()

# Create the workflow
class ReactSQLAndPlotWorkflow:
    def __init__(self):
        self.graph = create_workflow_graph()
        
    def run_workflow(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Execute the SQL and plotting workflow using a React agent.
        
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
            # Get the final insights from the agent
            final_insights = ""
            if len(final_state["messages"]) > 0:
                for msg in reversed(final_state["messages"]):
                    if msg.get("role") == "assistant" and msg.get("content"):
                        final_insights = msg.get("content")
                        break
            
            yield {
                "event": "workflow_complete",
                "content": {
                    "sql_result": final_state["sql_result"],
                    "plot_result": final_state["plot_result"],
                    "insights": final_insights
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
    
    # Create the graph visualization
    dot = graphviz.Digraph()
    
    # Add nodes
    dot.node("start", "Start", shape="ellipse")
    dot.node("agent", "React Agent", shape="box")
    dot.node("action", "Tool Executor", shape="box")
    dot.node("end", "End", shape="ellipse")
    
    # Add edges
    dot.edge("start", "agent")
    dot.edge("agent", "action", label="use tool")
    dot.edge("action", "agent", label="continue")
    dot.edge("action", "end", label="complete/error")
    
    # Save the graph
    graph_path = os.path.join(PLOTS_DIR, "workflow_graph.png")
    dot.render(os.path.splitext(graph_path)[0], format="png", cleanup=True)
    
    return graph_path

# For testing
if __name__ == "__main__":
    workflow = ReactSQLAndPlotWorkflow()
    query = "Show me the cost trends by model over the last week"
    
    for response in workflow.run_workflow(query):
        print(f"Event: {response['event']}")
        print(f"Content: {response['content']}")
    
    # Generate and display the graph visualization
    graph_path = plot_graph()
    print(f"Graph visualization saved to: {graph_path}")
