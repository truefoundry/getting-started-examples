"""
Content Builder Agent - Streamlit Web Interface

This Streamlit UI calls the FastAPI backend (your content builder agent service).
It displays:
- assistant response text
- links to generated markdown + images served by FastAPI (/files)
"""

from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import requests
import streamlit as st

# FastAPI base URL
API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")

SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "").rstrip("/")

def api(path: str) -> str:
    """Build URL to FastAPI endpoints considering optional root_path."""
    if SERVICE_ROOT_PATH:
        return f"{API_URL}{SERVICE_ROOT_PATH}{path}"
    return f"{API_URL}{path}"

st.set_page_config(page_title="AA Brown Bag Demo Agent", layout="wide")
st.title("📝 AA Brown Bag Demo Agent")

# Session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {role, content, meta}

with st.sidebar:
    st.header("Backend")
    st.caption("FastAPI URL")
    st.code(api(""), language="text")
    st.divider()

    st.divider()
    if st.button("New conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()

# ------------------------------
# Starter Prompts
# ------------------------------

STARTER_PROMPTS = [
    "Prepare a 5-minute executive talk track presenting Agentic Automation in the context of Automation Anywhere’s most recent product announcements in the last 6 months.",
    "Prepare a 5-minute customer presentation script on how LLMs and Automation Anywhere bots work together.",
    "Draft a structured implementation guide for securely deploying an AI copilot with Automation Anywhere.",
    "Create a customer-facing talk track focused on AI governance, tool access control, and data protection in Automation Anywhere workflows.",
]

if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""

st.markdown("### 🚀 Starter Ideas")

cols = st.columns(2)
for i, prompt in enumerate(STARTER_PROMPTS):
    with cols[i % 2]:
        if st.button(prompt, use_container_width=True):
            st.session_state.current_prompt = prompt
            st.rerun()

# ------------------------------
# Main input
# ------------------------------

user_task = st.text_area(
    "What do you want to create?",
    value=st.session_state.current_prompt,
    height=140,
    placeholder="Describe what you want to generate...",
)


run = st.button("Run agent", type="primary", use_container_width=True)

def call_agent(task: str):
    payload = {
        "thread_id": st.session_state.thread_id,
        "user_input": task,
    }
    resp = requests.post(api("/run_agent"), json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()

def file_url(rel_path: str) -> str:
    # FastAPI serves StaticFiles at /files
    return api(f"/files/{rel_path}")

if run:
    # Save user message
    st.session_state.history.append({"role": "user", "content": user_task})

    with st.spinner("Running agent..."):
        try:
            data = call_agent(user_task)

            # ---- Adjust these keys if your FastAPI response differs ----
            assistant_text = data.get("final_text") or data.get("response") or ""
            # ------------------------------------------------------------

            st.session_state.history.append({"role": "assistant", "content": assistant_text, "meta": data})

        except Exception as e:
            st.session_state.history.append({
                "role": "assistant",
                "content": f"Error calling backend: {e}"
            })

    st.rerun()

# Render conversation
st.subheader("Conversation")
for msg in st.session_state.history:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])