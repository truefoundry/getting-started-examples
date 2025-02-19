# Banking Agent using Langraph

This repository contains the code for the banking agent using Langraph. It can be used either via FastAPI or through streamlit.

## Installation

- Make sure you have `uv` installed. If not, refer: https://docs.astral.sh/uv/getting-started/installation/

- Install the dependencies:

```bash
uv sync
```

- Activate the environment:

```bash
source .venv/bin/activate
```

## Running the app

- Run the FastAPI app using

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

- Run the streamlit app using

```bash
streamlit run streamlit_app.py`
```
