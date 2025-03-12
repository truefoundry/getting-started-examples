from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Optional, Dict, Any
from clickhouse_tools import execute_clickhouse_query
from plot_tools import create_plot, parse_tabular_data
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
# Visualize the workflow using Ipython
from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

class SQLQueryResult(BaseModel):
    query: str
    column_names: list[str]
    rows: list[list[str]]
    error: Optional[str] = None
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert model to dictionary for API compatibility"""
        return {
            "query": self.query,
            "column_names": self.column_names,
            "rows": self.rows,
            "error": self.error
        }

class PlotResult(BaseModel):
    plot_type: str
    plot_path: str
    x_col: str
    y_col: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert model to dictionary for API compatibility"""
        return {
            "plot_type": self.plot_type,
            "plot_path": self.plot_path,
            "x_col": self.x_col,
            "y_col": self.y_col,
            "title": self.title,
            "error": self.error
        }

class VisualizationRequest(BaseModel):
    plot_type: str
    x_col: str
    y_col: Optional[str] = None
    title: Optional[str] = None
    hue: Optional[str] = None

class AgentState(TypedDict):
    query: str
    sql_result: SQLQueryResult
    plot_result: PlotResult

def sql_agent_node(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template("Generate a ClickHouse SQL query for: {query}")
    chain = prompt | ChatOpenAI(model="gpt-4o") | (lambda x: x.content) | execute_clickhouse_query
    sql_result = chain.invoke({"query": state["query"]})
    return {"query": state["query"], "sql_result": sql_result}

def plot_agent_node(state: AgentState) -> AgentState:
    sql_result = state["sql_result"]
    if sql_result.error:
        return {"query": state["query"], "sql_result": sql_result, "plot_result": PlotResult(plot_type="", plot_path="", x_col="", error=sql_result.error)}

    # Format data for parsing
    formatted_data = " | ".join(sql_result.column_names) + "\n" + "\n".join([" | ".join(row) for row in sql_result.rows])
    
    # First use parse_tabular_data to get a better understanding of the data
    try:
        # This will parse the data and convert to appropriate types
        df = parse_tabular_data(formatted_data)
        
        # Generate visualization recommendation based on the parsed data
        data_description = {
            "columns": df.columns.tolist(),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist(),
            "sample_rows": df.head(3).to_dict(orient='records')
        }
        
        # Enhanced prompt with data insights
        prompt = ChatPromptTemplate.from_template(
            """Given the data with the following characteristics:
            
            Columns: {columns}
            Data types: {dtypes}
            Numeric columns: {numeric_columns}
            Categorical columns: {categorical_columns}
            Datetime columns: {datetime_columns}
            Sample data: {sample_rows}
            
            Suggest the most appropriate visualization by providing:
            1. plot_type: Choose from 'line', 'bar', 'scatter', or 'histogram'
            2. x_col: The column for the x-axis
            3. y_col: The column for the y-axis (if applicable)
            4. title: A descriptive title for the plot
            5. hue: A column to use for color grouping (if applicable)
            
            Return your suggestion as a Python dictionary.
            """
        )
        
        # Get visualization recommendation
        chain = prompt | ChatOpenAI(model="gpt-4o") | (lambda x: VisualizationRequest(**eval(x.content)))
        viz_request = chain.invoke(data_description)
        
        # Create the plot using the recommendation
        plot_path = create_plot(
            data=formatted_data,
            plot_type=viz_request.plot_type,
            x_col=viz_request.x_col,
            y_col=viz_request.y_col,
            title=viz_request.title,
            hue=viz_request.hue
        )
        
        # Return the result
        return {
            "query": state["query"], 
            "sql_result": sql_result, 
            "plot_result": PlotResult(
                plot_type=viz_request.plot_type,
                plot_path=plot_path,
                x_col=viz_request.x_col,
                y_col=viz_request.y_col,
                title=viz_request.title
            )
        }
        
    except Exception as e:
        # Fallback to the original approach if parsing fails
        prompt = ChatPromptTemplate.from_template(
            "Given the data:\n{data}\nSuggest a visualization type, x_col, y_col, title, and hue if applicable."
        )
        chain = prompt | ChatOpenAI(model="gpt-4o") | (lambda x: VisualizationRequest(**eval(x.content))) | RunnableLambda(lambda req: create_plot(formatted_data, req.plot_type, req.x_col, req.y_col, req.title, req.hue))
        plot_result = chain.invoke({"data": formatted_data})
        return {"query": state["query"], "sql_result": sql_result, "plot_result": plot_result}

def create_workflow() -> StateGraph:
    """
    Creates and configures the workflow for SQL querying and plotting.
    
    Returns:
        StateGraph: Configured workflow graph with SQL and plotting nodes
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("plot_agent", plot_agent_node)
    workflow.set_entry_point("sql_agent")
    workflow.add_edge("sql_agent", "plot_agent")
    workflow.add_edge("plot_agent", END)
    return workflow

def display_workflow_graph(graph):
    """
    Displays the workflow graph visualization using Mermaid.
    
    Args:
        graph: The compiled workflow graph object
    """
    display(
        Image(
            graph.get_graph().draw_mermaid_png(
                draw_method=MermaidDrawMethod.API,
            )
        )
    )


if __name__ == "__main__":
    # Example usage

    workflow = create_workflow()
    graph = workflow.compile()
    display_workflow_graph(graph)

    # Invoke the graph
    result = graph.invoke({"query": "What is the total cost of all models?"})
    print(result)