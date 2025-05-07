import io
import os
import time
from datetime import datetime

import requests
import streamlit as st
from PIL import Image

# Configure the app
st.set_page_config(page_title="SQL and Plot Workflow", page_icon="📊", layout="wide")

# Add title and description
st.title("📊 SQL and Plot Workflow Dashboard")
st.markdown(
    """
This dashboard allows you to analyze data and generate visualizations using natural language queries.
Simply enter your query below and the CrewAI agents will generate the appropriate SQL query and visualization.
"""
)

# API endpoint configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def submit_query(query):
    """Submit a query to the CrewAI API"""
    response = requests.post(f"{API_BASE_URL}/query", json={"query": query})
    return response.json()


def check_status(job_id):
    """Check the status of a submitted job"""
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    return response.json()


def get_plot(job_id):
    """Get the generated plot for a completed job"""
    response = requests.get(f"{API_BASE_URL}/plot/{job_id}")
    return response.content


# Create the main query input
query = st.text_area(
    "Enter your query",
    placeholder="Example: Show me the cost trends by model over the last week. Filter models that show a 0 cost.",
    height=100,
)

# Add a submit button
if st.button("Generate Visualization"):
    if query:
        with st.spinner("Processing your query with CrewAI agents..."):
            try:
                # Submit the query
                result = submit_query(query)
                job_id = result.get("job_id")

                if not job_id:
                    st.error("Failed to submit query: No job ID received")
                else:
                    # Create containers for updates
                    status_container = st.empty()
                    event_container = st.empty()

                    # Poll for status
                    while True:
                        status_result = check_status(job_id)
                        current_status = status_result.get("status")

                        # Display events in reverse chronological order
                        if "events" in status_result and status_result["events"]:
                            events_text = ""
                            for event in reversed(status_result["events"]):
                                events_text += f"• {event['event']}: {event['content']}\n"
                            event_container.markdown(events_text)

                        # Update status
                        status_container.info(f"Status: {current_status}")

                        if current_status == "completed":
                            try:
                                # Get and display the plot
                                plot_data = get_plot(job_id)
                                image = Image.open(io.BytesIO(plot_data))
                                st.image(
                                    image, caption="Generated Visualization", use_column_width=True
                                )
                                st.success("Visualization generated successfully!")
                                break
                            except Exception as e:
                                st.error(f"Error displaying plot: {str(e)}")
                                break
                        elif current_status == "failed":
                            st.error(
                                f"Error: {status_result.get('error', 'Unknown error occurred')}"
                            )
                            break

                        time.sleep(1)  # Wait before checking again

            except Exception as e:
                st.error(f"Error processing request: {str(e)}")
    else:
        st.warning("Please enter a query first.")

# Add some helpful examples in the sidebar
st.sidebar.header("Example Queries")
st.sidebar.markdown(
    """
Here are some example queries you can try:

- Show me the cost trends by model over the last week. Filter models that show a 0 cost.
- Compare usage patterns across the top 5 models
- List the top 5 most active users by request count in the last 30 days.

"""
)

# Add information about the project
st.sidebar.header("About")
st.sidebar.markdown(
    """
This dashboard provides a user-friendly interface to the SQL and Plot Workflow API powered by CrewAI agents.

**Features:**
- Submit natural language queries
- Track agent processing in real-time
- View SQL query generation
- See visualization creation steps
- Download generated plots

**How it works:**
1. Your query is processed by the SQL Writer agent
2. SQL is generated and executed
3. Results are analyzed by the Plot Writer agent
4. Appropriate visualization is created
5. Results are displayed in real-time
"""
)

# Add footer with version info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Version:** 1.0.0 • **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")
