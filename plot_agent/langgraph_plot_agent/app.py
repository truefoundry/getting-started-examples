import io
import logging
import os
import time

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(".env")

# Configure the app
st.set_page_config(page_title="SQL and Plot Workflow", page_icon="📊", layout="wide")

# Hide default Streamlit elements
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Add title
st.title("📊 Plot Generator")

# API endpoint configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not API_BASE_URL:
    st.error("Error: API_BASE_URL environment variable is not set. Please set it to your API endpoint URL.")
    st.stop()


def submit_query(query):
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            timeout=10,  # Add timeout to prevent hanging
        )
        response.raise_for_status()  # Raise error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error submitting query: {e}")
        raise Exception(f"Failed to submit query: {e}")


def check_status(job_id):
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking status for job {job_id}: {e}")
        raise Exception(f"Failed to check job status: {e}")


def get_plot(job_id):
    try:
        response = requests.get(f"{API_BASE_URL}/plot/{job_id}", timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting plot for job {job_id}: {e}")
        if hasattr(e.response, "content"):
            logger.error(f"Response content: {e.response.content}")
        raise Exception(f"Failed to retrieve plot: {e}")


# Create the main query input
query = st.text_area(
    "Enter your query",
    placeholder="Example: Show me the cost trends by model over the last week. Filter models that show a 0 cost.",
    height=100,
)

# Add a submit button
if st.button("Generate Visualization"):
    if query:
        try:
            # Simple status message placeholder
            status_placeholder = st.empty()
            status_placeholder.info("Processing your query... Please wait.")

            # Submit the query
            result = submit_query(query)
            job_id = result.get("job_id")

            # Poll for status without showing intermediate results
            max_retries = 30  # About 30 seconds max wait time
            retries = 0

            while retries < max_retries:
                try:
                    status_result = check_status(job_id)
                    current_status = status_result.get("status")

                    if current_status == "completed" or (
                        current_status == "failed" and status_result.get("plot_result") is not None
                    ):
                        try:
                            # Clear status message
                            status_placeholder.empty()

                            # Get and display only the plot
                            plot_data = get_plot(job_id)
                            image = Image.open(io.BytesIO(plot_data))
                            st.image(image, use_column_width=True)
                            break
                        except Exception as plot_error:
                            logger.error(f"Error displaying plot: {plot_error}")
                            status_placeholder.error("Could not retrieve visualization.")
                            break
                    elif current_status == "failed":
                        status_placeholder.error("Could not generate visualization from your query.")
                        break

                    # Only update processing message if still running
                    if retries % 5 == 0:  # Update message every 5 seconds
                        status_placeholder.info("Processing your query... Please wait.")

                    retries += 1
                    time.sleep(1)  # Wait before checking again
                except Exception as status_error:
                    logger.error(f"Error checking job status: {status_error}")
                    retries += 1
                    time.sleep(1)

            if retries >= max_retries:
                status_placeholder.warning("Request is taking longer than expected. Please try again later.")

        except Exception as e:
            st.error("An error occurred. Please try again.")
            logger.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a query first.")

# Add some helpful examples in the sidebar
st.sidebar.header("Example Queries")
st.sidebar.markdown(
    """
- Show me the cost trends by model over the last week
- Compare usage patterns across the top 5 models
- List the top 5 most active users by request count in the last 30 days
- Show token usage by model for the past month
"""
)

# Add information about the project
st.sidebar.header("About")
st.sidebar.markdown(
    """
This dashboard provides a user-friendly interface to the SQL and Plot Workflow API.
It allows you to:
- Submit natural language queries
- Track query processing in real-time
- View generated visualizations
- Download results
"""
)
