import asyncio
import uuid

import streamlit as st
from src.agent.graph import run_agent

# please note that the location of this function has changed multiple times in the last versions of streamlit
from streamlit.runtime.scriptrunner import get_script_run_ctx

# if run directly, print a warning
ctx = get_script_run_ctx()
if ctx is None:
    print("************")
    print("PLEASE NOTE: run this app with `streamlit run streamlit_app.py`")
    print("************")
    exit(1)

# Suggested questions
SUGGESTED_QUESTIONS = [
    "Can you check my savings account balance?",
    "Can you transfer $10 from savings to current account?",
]


def initialize_session_state():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "I'm your Banking Assistant. How may I help you?",
            }
        ]


async def process_input(user_input):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = await run_agent(st.session_state.thread_id, user_input)
            if response and response.get("response"):
                st.write(response["response"])
                st.session_state.messages.append({"role": "assistant", "content": response["response"]})


# Initialize session state
initialize_session_state()

# Set page config
st.set_page_config(page_title="Banking Assistant")
st.title("💬 Banking Assistant Agent")

with st.sidebar:
    st.header("Suggested Questions")
    for question in SUGGESTED_QUESTIONS:
        if st.button(question, key=question, use_container_width=True):
            asyncio.run(process_input(question))
            st.rerun()

    # Add file upload widget in sidebar
    st.header("Upload File")
    uploaded_file = st.file_uploader("Upload a text file", type=["txt"])
    if uploaded_file is not None:
        file_contents = uploaded_file.getvalue().decode("utf-8")
        if st.button("Process File"):
            asyncio.run(process_input(file_contents))
            st.rerun()

# Display existing chat messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Prompt for user input and save
if prompt := st.chat_input("Type your message here..."):
    asyncio.run(process_input(prompt))
    st.rerun()
