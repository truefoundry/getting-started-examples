import os
import uuid
from pathlib import Path

import requests
import streamlit as st

# Configuration for the FastAPI endpoint (adjust if necessary)
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://localhost:8000")

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

    # Call /init with the filename
    payload = {"filename": unique_filename}
    response = requests.post(f"{API_BASE_URL}/init", json=payload)

    if response.status_code == 200:
        st.success("Document initialized successfully!")
    else:
        # Clean up the file if initialization failed
        os.remove(file_path)
        st.error(f"Error: {response.json()['detail']}")

# Chat interface
st.header("Chat with Your Document")
user_query = st.text_input("Enter your question:")

if st.button("Send"):
    if user_query:
        infer_url = f"{API_BASE_URL}/infer"
        payload = {"query": user_query}
        with st.spinner("Getting response..."):
            response = requests.post(infer_url, json=payload)
        if response.status_code == 200:
            answer = response.json().get("answer", "")
            st.markdown("### Response")
            st.write(answer)
        else:
            st.error(f"Inference failed: {response.text}")
    else:
        st.warning("Please enter a question.")
