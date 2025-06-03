import os
import sys
import uuid
from pathlib import Path

import requests
import streamlit as st
from config.settings import settings

# Add root directory to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Create uploaded_files directory if it doesn't exist
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)

# Page Title
st.markdown("## 📄 Document Chat with FastAPI Inference")

# File uploader section
st.markdown("### 📤 Upload a Document")
uploaded_file = st.file_uploader("Choose a document", type=["txt", "pdf"])

# Reset session state when a new file is uploaded
if uploaded_file is not None:
    current_file_name = getattr(st.session_state, "current_file_name", None)

    if current_file_name != uploaded_file.name:
        # Clear session state to remove previous chat & reset UI
        st.session_state.clear()
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.uploaded = False  # Hide chat until processing is done
        st.session_state.user_query = ""  # Clear input state

        # Remove previously uploaded file (if exists)
        if "file_path" in st.session_state:
            old_file = Path(st.session_state.file_path)
            if old_file.exists():
                old_file.unlink()  # Delete old file

        # Generate unique filename for new upload
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save the new file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.file_path = str(file_path)

        # Show loading spinner
        with st.spinner("🛠 Processing document... Getting it ready for Q&A!"):
            try:
                with open(file_path, "rb") as f:
                    files = {"file": (unique_filename, f, "application/octet-stream")}
                    response = requests.post(f"{settings.API_URL}/init", files=files, timeout=60)

                if response.status_code == 200:
                    st.success("✅ Document uploaded & initialized successfully!")
                    st.session_state.uploaded = True
                    st.rerun()  # Force rerun to refresh UI
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"❌ Error: {error_detail}")
                    file_path.unlink(missing_ok=True)  # Clean up
                    st.session_state.uploaded = False
            except requests.exceptions.RequestException as e:
                file_path.unlink(missing_ok=True)
                st.error(f"❌ Connection error: {str(e)}")
                st.session_state.uploaded = False

# Only show chat if document is fully processed and uploaded
if "uploaded" in st.session_state and st.session_state.uploaded:
    st.markdown("### 💬 Chat with Your Document")

    with st.form(key="chat_form"):
        user_query = st.text_input("📝 Enter your question:", key="user_query", value="")
        submit_button = st.form_submit_button("🚀 Send")

    if submit_button and user_query:
        infer_url = f"{settings.API_URL}/infer"
        payload = {"query": user_query}

        with st.spinner("🤖 Thinking..."):
            try:
                response = requests.post(infer_url, json=payload)
                if response.status_code == 200:
                    answer = response.json().get("answer", "")
                    st.markdown("### 👨‍💬 Response")
                    st.write(answer)
                else:
                    error_message = response.json().get("detail", response.text)
                    st.error(f"❌ Inference failed: {error_message}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
    elif submit_button:
        st.warning("⚠️ Please enter a question.")
