from agent import SQLAndPlotWorkflow, SQLQueryResult
from agno.utils.log import logger
import logging
import traceback

# Set up logging to see detailed output
logger.setLevel(logging.INFO)

def test_workflow():
    """Test the SQL and Plot workflow with various queries."""
    workflow = SQLAndPlotWorkflow()
    
    # List of test queries
    test_queries = [
        # Simple cost analysis
        "Show me the average cost per model for the last 24 hours",
        
        # Time series analysis
        "Plot the latency trends for different models over the past week",
        
        # Distribution analysis
        "Show me the distribution of input tokens across different request types",
        
        # Error analysis
        "What are the most common error codes and their frequencies?",
        
        # Complex analysis
        "Compare the cost and latency relationship for different models"
    ]
    
    # Run each test query
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Testing query: {query}")
        print(f"{'='*50}")
        
        try:
            for response in workflow.run_workflow(query):
                print(f"\nEvent: {response.event}")
                if hasattr(response.content, 'model_dump'):
                    print("Content:", response.content.model_dump())
                else:
                    print("Content:", response.content)
        except Exception as e:
            print(f"Error running query: {str(e)}")
            traceback.print_exc()

def test_single_query(query: str):
    """Test the workflow with a single query."""
    workflow = SQLAndPlotWorkflow()
    
    print(f"\n{'='*50}")
    print(f"Testing query: {query}")
    print(f"{'='*50}")
    
    try:
        for response in workflow.run_workflow(query):
            print(f"\nEvent: {response.event}")
            if hasattr(response.content, 'model_dump'):
                print("Content:", response.content.model_dump())
            else:
                print("Content:", response.content)
    except Exception as e:
        print(f"Error running query: {str(e)}")
        traceback.print_exc()

def debug_visualization_only():
    """
    Test only the visualization part of the workflow with mock SQL data.
    This is useful for debugging visualization issues without running SQL queries.
    """
    workflow = SQLAndPlotWorkflow()
    
    # Create a mock SQL result
    sample_data = """
    created_at | cost | model_name
    2023-01-01 | 0.1 | gpt-4
    2023-01-02 | 0.2 | gpt-3.5
    2023-01-03 | 0.15 | gpt-4
    2023-01-04 | 0.25 | gpt-3.5
    2023-01-05 | 0.18 | gpt-4
    """
    
    mock_sql_result = SQLQueryResult(
        query="SELECT created_at, cost, model_name FROM request_logs ORDER BY created_at",
        data=sample_data.strip(),
        error=None
    )
    
    print(f"\n{'='*50}")
    print("Testing visualization with mock SQL data")
    print(f"{'='*50}")
    
    try:
        # Directly test the visualization part
        for response in workflow._create_visualization(mock_sql_result):
            print(f"\nEvent: {response.event}")
            if hasattr(response.content, 'model_dump'):
                print("Content:", response.content.model_dump())
            else:
                print("Content:", response.content)
    except Exception as e:
        print(f"Error in visualization: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    # Option 1: Run all test queries
    # test_workflow()
    
    # Option 2: Test a specific query
    test_single_query("Show me the cost distribution by model for the last week")
    
    # Option 3: Debug visualization only
    # debug_visualization_only()
    
    # Option 4: Interactive mode
    """
    while True:
        query = input("\nEnter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        test_single_query(query)
    """ 