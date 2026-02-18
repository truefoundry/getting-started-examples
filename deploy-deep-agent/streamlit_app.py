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

st.set_page_config(page_title="Content Builder Agent", layout="wide")
st.title("📝 Content Builder Agent")

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
    "Create a LinkedIn post about AI agents",
    "Write a blog post about AI agents",
    "Create a LinkedIn post about prompt engineering",
    "Write a Twitter thread about the future of coding",
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

st.divider()
st.subheader("Outputs preview (from FastAPI /files)")

# Find the latest assistant message meta that contains platform/slug/files
latest_meta = None
for msg in reversed(st.session_state.history):
    if msg.get("role") == "assistant" and isinstance(msg.get("meta"), dict):
        latest_meta = msg["meta"]
        break

if not latest_meta:
    st.info("Run the agent once to see outputs here.")
    st.stop()

platform = latest_meta.get("platform")
slug = latest_meta.get("slug")
files = latest_meta.get("files") or {}

if not platform or not slug:
    st.info("No platform/slug returned by backend yet. Ensure the agent called write_file.")
    st.stop()

# Prefer file paths returned by backend (relative paths), fallback to convention
md_rel = files.get("markdown") or f"{platform}/{slug}/post.md"
hero_rel = files.get("hero_image") or f"blogs/{slug}/hero.png"
social_rel = files.get("social_image") or f"{platform}/{slug}/image.png"

md_link = file_url(md_rel)
hero_link = file_url(hero_rel)
social_link = file_url(social_rel)

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Markdown")
    st.markdown(f"- **Path:** `{md_rel}`")
    st.markdown(f"- **Link:** {md_link}")

    try:
        r = requests.get(md_link, timeout=10)
        if r.status_code == 200 and r.text.strip():
            st.markdown(r.text)
        else:
            st.info("Markdown not found yet. The agent may not have written the file (or wrote to a different OUTPUT_DIR).")
    except Exception as e:
        st.info(f"Could not fetch markdown: {e}")

with c2:
    st.markdown("### Images")

    st.markdown(f"- Hero: {hero_link}")
    try:
        r = requests.get(hero_link, timeout=5)
        if r.status_code == 200:
            st.image(hero_link, caption=hero_rel, use_container_width=True)
        else:
            st.caption("No hero image found.")
    except Exception as e:
        st.caption(f"Could not fetch hero image: {e}")

    st.markdown(f"- Social: {social_link}")
    try:
        r = requests.get(social_link, timeout=5)
        if r.status_code == 200:
            st.image(social_link, caption=social_rel, use_container_width=True)
        else:
            st.caption("No social image found.")
    except Exception as e:
        st.caption(f"Could not fetch social image: {e}")
