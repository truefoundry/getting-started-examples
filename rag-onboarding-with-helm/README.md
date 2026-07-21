# RAG on TrueFoundry with Helm (Qdrant)

A Retrieval Augmented Generation (RAG) application deployed on the TrueFoundry platform as **Helm applications**:

- **Qdrant** — vector database deployed from the [official Qdrant Helm chart](https://qdrant.github.io/qdrant-helm) via a public Helm repository (TrueFoundry `type: helm-repo`, same pattern as Bitnami charts). **Bitnami does not publish a Qdrant chart**, so this repo uses the official Qdrant chart.
- `charts/rag-app` — A FastAPI service that ingests `.txt`/`.pdf` documents, embeds them via the TrueFoundry LLM Gateway, stores vectors in Qdrant, and answers questions using retrieved context.

```
rag-onboarding-with-helm/
├── app/                          # FastAPI RAG service source code + Dockerfile
│   ├── main.py                   # API endpoints (/documents, /query, /health)
│   ├── rag_pipeline.py           # Chunking, embedding, retrieval, generation
│   ├── settings.py               # Env-driven configuration (load_dotenv)
│   ├── requirements.txt
│   └── Dockerfile
├── charts/
│   └── rag-app/                  # Helm chart: RAG API (Deployment + Service + Ingress)
├── deploy/
│   ├── qdrant.truefoundry.yaml   # TrueFoundry Helm app: official Qdrant chart
│   ├── rag-app.truefoundry.yaml  # TrueFoundry Helm app: RAG API
│   └── deploy.py                 # SDK deploy of both
├── testdata/
│   └── sample.txt
├── docker-compose.yml            # Local Qdrant + optional API
└── .env.example
```



## How it works

1. `POST /documents` — upload a `.txt` or `.pdf` file. The service splits it into chunks, generates embeddings through the TrueFoundry LLM Gateway, and stores them in a Qdrant collection.
2. `POST /query` — the question is embedded, the top-k most similar chunks are retrieved from Qdrant, and an LLM generates an answer grounded in that context.
3. `DELETE /documents` — drops the Qdrant collection.



## Prerequisites

- A TrueFoundry account with a cluster and [workspace](https://docs.truefoundry.com/docs/key-concepts#workspace)
- Models enabled on the [TrueFoundry LLM Gateway](https://www.truefoundry.com/docs/ai-gateway/intro-to-llm-gateway) (one chat model + one embedding model) and a TrueFoundry API key
- A container registry the cluster can pull from (for the RAG app image)
- [TrueFoundry CLI](https://docs.truefoundry.com/docs/setup-cli): `pip install truefoundry && tfy login --host https://<your-org>.truefoundry.cloud`



## Deploy on TrueFoundry



### Step 1 — Deploy Qdrant (official Helm chart)

Edit `deploy/qdrant.truefoundry.yaml` and set a real `workspace_fqn` (from the TrueFoundry UI: Workspaces → Copy FQN).

`tfy apply` does **not** load `.env` or expand `${VAR}` — use concrete values in the YAML (already filled for this workspace), or:

```bash
python deploy/apply_manifest.py deploy/qdrant.truefoundry.yaml
```

Or directly:

```bash
tfy apply -f deploy/qdrant.truefoundry.yaml
```

This installs chart `qdrant` version `1.18.2` from `https://qdrant.github.io/qdrant-helm` as release `qdrant` (REST on port **6333**).

### Step 2 — Build and push the RAG app image

```bash
cd app
docker build --platform linux/amd64 -t <registry>/rag-app:0.1.0 .
docker push <registry>/rag-app:0.1.0
```



### Step 3 — Deploy the RAG app Helm chart

Edit `deploy/rag-app.truefoundry.yaml` and fill in:

- `workspace_fqn` — same workspace as Step 1
- `values.image.repository` / `tag` — the image from Step 2
- `values.config.truefoundry.llmGatewayBaseUrl`
- `values.config.llmModel` / `embeddingModel` / `embeddingDimensions`
- the `kustomize.additions` Secret manifest — replace the `tfy-secret://...`
  FQN with your own TrueFoundry secret FQN and set the Secret's `namespace`
  to your workspace's namespace

> **Note:** `tfy-secret://` FQNs are only resolved inside Kubernetes Secret
> manifests added via `kustomize.additions` (using `stringData`). They are
> **not** resolved inside Helm `values`, so never put an FQN in
> `values.config.truefoundry.apiKey` or `existingSecret` — the latter must be
> the name of a real Kubernetes Secret.

```bash
tfy apply -f deploy/rag-app.truefoundry.yaml
```

The app connects to Qdrant at `qdrant:6333` in the same namespace.

> Or deploy both via the Python SDK after filling `.env`:
>
> ```bash
> source .venv/bin/activate
> python -m pip install -r deploy/requirements.txt
> python deploy/deploy.py
> ```

You can also deploy from the TrueFoundry UI: **New Deployment → show advanced → Helm**:

- Qdrant: **Helm repository** → URL `https://qdrant.github.io/qdrant-helm`, chart `qdrant`, version `1.18.2`
- RAG app: **Git repository** → this repo, path `rag-onboarding-with-helm/charts/rag-app`, revision `chintan-rag-onboarding-with-helm`



### Step 4 — Try it out

```bash
kubectl port-forward svc/rag-app 8000:8000 -n <workspace-namespace>
```

```bash
curl -X POST http://localhost:8000/documents -F "file=@my-document.pdf"
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

Interactive API docs are served at `/`.

## Run locally



### Option A — Docker Compose (Qdrant + API)

```bash
cp .env.example .env   # LOCAL_FAKE_LLM=true works without a TFY API key
docker compose up --build
```

API: [http://localhost:8000/](http://localhost:8000/)

### Option B — Qdrant in Docker, app from a virtual environment

```bash
# 1. Start Qdrant
docker compose up -d qdrant

# 2. Create and activate a local virtual environment
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt

# 3. Run the API
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Smoke test:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/documents -F "file=@testdata/sample.txt"
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Where are embeddings stored?"}'
```

Set `LOCAL_FAKE_LLM=false` and fill `TFY_API_KEY` / `TFY_LLM_GATEWAY_BASE_URL` in `.env` to use the real LLM Gateway.

## Configuration reference


| Variable                       | Example                              | Description                                            |
| ------------------------------ | ------------------------------------ | ------------------------------------------------------ |
| `QDRANT_HOST` / `QDRANT_PORT`  | `qdrant` / `6333`                    | Qdrant REST endpoint                                   |
| `QDRANT_API_KEY`               | *(empty)*                            | Optional Qdrant API key                                |
| `TFY_API_KEY`                  | —                                    | TrueFoundry API key for the LLM Gateway                |
| `TFY_LLM_GATEWAY_BASE_URL`     | —                                    | OpenAI-compatible base URL of the LLM Gateway          |
| `LOCAL_FAKE_LLM`               | `false`                              | Use local fake embeddings (no API key) for smoke tests |
| `LLM_MODEL`                    | `openai-main/gpt-4o-mini`            | Chat model ID on the gateway                           |
| `EMBEDDING_MODEL`              | `openai-main/text-embedding-3-small` | Embedding model ID                                     |
| `EMBEDDING_DIMENSIONS`         | `1536`                               | Vector size for Qdrant collection create               |
| `COLLECTION_NAME`              | `documents`                          | Qdrant collection name                                 |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200`                       | Text splitting parameters                              |
| `SIMILARITY_TOP_K`             | `5`                                  | Number of chunks retrieved per query                   |


