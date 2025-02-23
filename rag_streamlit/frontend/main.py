import os
import sys
import uuid
from pathlib import Path

# Add root directory to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

import requests
import streamlit as st
from config.settings import settings

# Create uploaded_files directory if it doesn't exist
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)

st.title("Document Chat with FastAPI Inference")

# File uploader for the document
st.header("Upload a Document")
uploaded_file = st.file_uploader("Choose a document", type=["txt", "pdf", "doc"])

if uploaded_file is not None:
    # Generate unique filename with original extension
    file_extension = os.path.splitext(uploaded_file.name)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        # Save file to data directory

    # Send the file to the API using multipart/form-data
    with open(file_path, "rb") as f:
        files = {"file": (unique_filename, f, "application/octet-stream")}
        try:
            response = requests.post(f"{settings.API_URL}/init", files=files)
            if response.status_code == 200:
                st.success("Document initialized successfully!")
            else:
                # Clean up the file if initialization failed
                os.remove(file_path)
                try:
                    error_detail = response.json().get("detail", "Unknown error occurred")
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text or f"HTTP {response.status_code}"
                st.error(f"Error: {error_detail}")
        except requests.exceptions.RequestException as e:
            os.remove(file_path)
            st.error(f"Connection error: {str(e)}")

# Chat interface
st.header("Chat with Your Document")
user_query = st.text_input("Enter your question:")

if st.button("Send"):
    if user_query:
        infer_url = f"{settings.API_URL}/infer"
        payload = {"query": user_query}
        with st.spinner("Getting response..."):
            try:
                response = requests.post(infer_url, json=payload)
                if response.status_code == 200:
                    try:
                        answer = response.json().get("answer", "")
                        st.markdown("### Response")
                        st.write(answer)
                    except requests.exceptions.JSONDecodeError:
                        st.error("Received invalid response format from server")
                else:
                    try:
                        error_message = response.json().get("detail", response.text)
                    except requests.exceptions.JSONDecodeError:
                        error_message = response.text or f"HTTP {response.status_code}"
                    st.error(f"Inference failed: {error_message}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    else:
        st.warning("Please enter a question.")
