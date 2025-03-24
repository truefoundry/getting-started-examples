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
""")

# API endpoint configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not API_BASE_URL:
    st.error("Error: API_BASE_URL environment variable is not set. Please set it to your API endpoint URL.")
    st.stop()

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
            
            # Poll for status
            while True:
                status_result = check_status(job_id)
                current_status = status_result.get("status")
                
                # Display events
                if "events" in status_result:
                    for event in status_result["events"]:
                        status_container.info(f"{event['event']}: {event['content']}")
                
                if current_status == "completed":
                    # Get and display the plot
                    plot_data = get_plot(job_id)
                    image = Image.open(io.BytesIO(plot_data))
                    st.image(image, caption="Generated Visualization", use_column_width=True)
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
- Show me the cost trends by model over the last week. Filter models that show a 0 cost.
- Compare usage patterns across the top 5 models
- List the top 5 most active users by request count in the last 30 days.
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
""") 