import streamlit as st
import requests
import time
from PIL import Image
import io
import os

# Configure the app
st.set_page_config(
    page_title="SQL and Plot Workflow",
    page_icon="📊",
    layout="wide"
)

# Add title and description
st.title("📊 SQL and Plot Workflow Dashboard")
st.markdown("""
This dashboard allows you to analyze data and generate visualizations using natural language queries.
Simply enter your query below and the system will generate the appropriate SQL query and visualization.

This implementation uses LangGraph for the agent framework.
""")

# API endpoint configuration
API_BASE_URL = "http://localhost:8000"

def submit_query(query):
    response = requests.post(
        f"{API_BASE_URL}/query",
        json={"query": query}
    )
    return response.json()

def check_status(job_id):
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    return response.json()

def get_plot(job_id):
    response = requests.get(f"{API_BASE_URL}/plot/{job_id}")
    return response.content

def get_workflow_graph():
    response = requests.get(f"{API_BASE_URL}/graph")
    return response.content

# Add a button to view the workflow graph
if st.button("View LangGraph Workflow"):
    try:
        with st.spinner("Generating workflow graph..."):
            graph_data = get_workflow_graph()
            image = Image.open(io.BytesIO(graph_data))
            st.image(image, caption="LangGraph Workflow Visualization", use_column_width=True)
    except Exception as e:
        st.error(f"Error displaying workflow graph: {e}")

# Create the main query input
query = st.text_area(
    "Enter your query",
    placeholder="Example: Show me the cost trends by model over the last week. Filter models that show a 0 cost.",
    height=100
)

# Add a submit button
if st.button("Generate Visualization"):
    if query:
        with st.spinner("Processing your query..."):
            # Submit the query
            result = submit_query(query)
            job_id = result.get("job_id")
            
            # Create placeholder for status updates
            status_container = st.empty()
            events_container = st.container()
            
            # Poll for status
            while True:
                status_result = check_status(job_id)
                current_status = status_result.get("status")
                
                # Display events
                if "events" in status_result:
                    events_container.empty()
                    with events_container:
                        for event in status_result["events"]:
                            event_type = event['event']
                            content = event['content']
                            
                            if event_type == "workflow_error":
                                st.error(f"Error: {content}")
                            elif event_type == "visualization_error":
                                st.warning(f"Visualization Error: {content}")
                            elif event_type == "visualization_complete":
                                st.success("Visualization complete!")
                            elif event_type == "sql_complete":
                                st.info("SQL query executed successfully!")
                            elif event_type == "workflow_complete":
                                st.success("Workflow completed successfully!")
                            else:
                                st.info(f"{event_type}: {content}")
                
                # Update status
                status_container.info(f"Status: {current_status}")
                
                if current_status == "completed":
                    # Get and display the plot
                    try:
                        plot_data = get_plot(job_id)
                        image = Image.open(io.BytesIO(plot_data))
                        st.image(image, caption="Generated Visualization", use_column_width=True)
                    except Exception as e:
                        st.error(f"Error displaying plot: {e}")
                    break
                elif current_status == "failed":
                    st.error(f"Error: {status_result.get('error')}")
                    break
                
                time.sleep(1)  # Wait before checking again
    else:
        st.warning("Please enter a query first.")

# Add some helpful examples in the sidebar
st.sidebar.header("Example Queries")
st.sidebar.markdown("""
- Show me the cost trends by model over the last week
- Compare usage patterns across different models
- Display daily active users over time
- Analyze error rates by model type
- Show me the distribution of latency by model
- What are the top 5 models by cost?
""")

# Add information about the project
st.sidebar.header("About")
st.sidebar.markdown("""
This dashboard provides a user-friendly interface to the SQL and Plot Workflow API.
It allows you to:
- Submit natural language queries
- Track query processing in real-time
- View generated visualizations
- Download results

This implementation uses LangGraph for the agent framework.
""")

# Add a footer
st.markdown("---")
st.markdown("Built with Streamlit, FastAPI, and LangGraph") 