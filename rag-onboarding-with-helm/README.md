# RAG on TrueFoundry with Helm (Qdrant) from Git Private **Repository**

A Retrieval-Augmented Generation (RAG) application deployed on the TrueFoundry platform as **Helm applications**:

- **Qdrant** — vector database from the [official Qdrant Helm chart](https://qdrant.github.io/qdrant-helm) via a public Helm repository (TrueFoundry `type: helm-repo`). **Bitnami does not publish a Qdrant chart**, so this repo uses the official chart.
- `charts/rag-app` — a FastAPI service that ingests `.txt`/`.pdf` documents, embeds them via the TrueFoundry LLM Gateway, stores vectors in Qdrant, and answers questions using retrieved context.

```
rag-onboarding-with-helm/
├── app/                          # FastAPI RAG service + Dockerfile
│   ├── main.py                   # API endpoints (/documents, /query, /health)
│   ├── rag_pipeline.py           # Chunking, embedding, retrieval, generation
│   ├── settings.py               # Env-driven configuration
│   ├── requirements.txt
│   └── Dockerfile
├── charts/
│   └── rag-app/                  # Helm chart: Deployment + Service + Ingress
├── deploy/
│   ├── qdrant.truefoundry.yaml   # TrueFoundry Helm app: official Qdrant chart
│   ├── rag-app.truefoundry.yaml  # TrueFoundry Helm app: RAG API (+ Secret via kustomize)
│   ├── apply_manifest.py         # Load .env, expand ${VAR}, then tfy apply
│   └── deploy.py                 # SDK deploy of both apps
├── testdata/
│   └── sample.txt
├── docker-compose.yml            # Local Qdrant + optional API
└── .env.example
```



## How it works?

1. `POST /documents` — upload a `.txt` or `.pdf` file. The service splits it into chunks, generates embeddings through the TrueFoundry LLM Gateway, and stores them in a Qdrant collection.
2. `POST /query` — the question is embedded, the top-k most similar chunks are retrieved from Qdrant, and an LLM generates an answer grounded in that context.
3. `DELETE /documents` — drops the Qdrant collection.



## Prerequisites

- A TrueFoundry account with a cluster and [workspace](https://docs.truefoundry.com/docs/key-concepts#workspace)
- Models enabled on the [TrueFoundry LLM Gateway](https://www.truefoundry.com/docs/ai-gateway/intro-to-llm-gateway) (one chat model + one embedding model) and a TrueFoundry API key stored as a TrueFoundry secret
- A container registry the cluster can pull from (for the RAG app image)
- [TrueFoundry CLI](https://docs.truefoundry.com/docs/setup-cli):

```bash
pip install truefoundry
tfy login --host https://<your-org>.truefoundry.cloud
```

In this case,

```bash
tfy login --host https://tfy-eo.truefoundry.cloud
```

If you set `TFY_API_KEY` in the environment (for example via `.env`), you must also set `TFY_HOST` to the same control-plane URL. Otherwise unset `TFY_API_KEY` and rely on `tfy login`.

## Initial setup

- Try to follow steps from [Deploy Helm Charts](https://www.truefoundry.com/docs/deploy-helm-charts)
- For this example, I deployed the Helm Chart with **Option 3: Git Repository**
  - Follow the steps from [Option 3: Git Private Repository](https://www.truefoundry.com/docs/deploy-helm-charts#github-private-repository)
    - From that, follow step 1, 2, and 4.
    - Skip step 3 as it's not required really. Instead check the deploy/rag-app.truefoundry.yaml file, and check how the secrets are mentioned under `kustomize` and how is it referenced under `values.config.truefoundry.existingSecret`.
    - Following as per the step 3 (Deploy Repository Secret using Kubernetes Manifest) will throw errors as below: `one or more synchronization tasks are not valid`. This is because the repository secret must be deployed as a separate Kubernetes Manifest deployment (not bundled with your Helm chart deployment).



## Deploy on TrueFoundry



### Step 1 — Deploy Qdrant (official Helm chart)

Edit `deploy/qdrant.truefoundry.yaml` and set a real `workspace_fqn` (TrueFoundry UI: Workspaces → Copy FQN).

`tfy apply` does **not** load `.env` or expand `${VAR}` — use concrete values in the YAML, or:

```bash
python deploy/apply_manifest.py deploy/qdrant.truefoundry.yaml
```

Or apply directly:

```bash
tfy apply -f deploy/qdrant.truefoundry.yaml
```

This installs chart `qdrant` version `1.18.2` from `https://qdrant.github.io/qdrant-helm` as release `qdrant` (REST on port **6333**).

Once deployed successfully, you can see it as running in the `Healthy` status under [Deployments](https://tfy-eo.truefoundry.cloud/deployments?tab=helms).

### Step 2 — Build and push the RAG app docker image to Docker Hub

```bash
cd app
docker login
docker build --platform linux/amd64 -t <registry>/rag-app:latest .
docker push <registry>/rag-app:latest
```

Example in this case to push to the Docker Hub:

```bash
docker build --platform linux/amd64 -t cdonda/rag-app:latest .
docker push cdonda/rag-app:latest
```

Verify that the image is pushed successfully to the Docker Hub. To check this: Open Docker Desktop -> Go to Docker Hub (towards last on the left side panel) -> Search for your registry/user name (ex: cdonda) -> Select your registry (ex: cdonda/rag-app) -> Go to Tags -> Check if the image is present or not.

Use `--platform linux/amd64` when building on Apple Silicon so the cluster can pull the image.

### Step 3 — Deploy the RAG app Helm Chart

Edit `deploy/rag-app.truefoundry.yaml` and fill in:

- `workspace_fqn` — same workspace as Step 1
- `values.image.repository` / `tag` — the image from Step 2 (default tag: `latest`)
- `values.config.truefoundry.llmGatewayBaseUrl` / `host`
- `values.config.llmModel` / `embeddingModel` / `embeddingDimensions`
- `kustomize.additions` Secret — replace the `tfy-secret://...` FQN with your own TrueFoundry secret FQN, and set the Secret's `namespace` to your workspace namespace

> **Important — secrets:** `tfy-secret://` FQNs are only resolved inside Kubernetes Secret manifests added via `kustomize.additions` (`stringData`). They are **not** resolved inside Helm `values`. These secrets are resolved/patched at the deployment time.
>
> In the rag-app.truefoundry.yaml file, leave `values.config.truefoundry.apiKey/apiPrefix` under qdrant and truefoundry sections empty.
>
> - Set `values.config.truefoundry.existingSecret` to a real Kubernetes Secret name (e.g. `rag-app-tfy-creds`), **not** a `tfy-secret://` FQN.
> - Put the `tfy-secret://...` FQN in the `kustomize.additions` Secret's `stringData.TFY_API_KEY`.
>
> In the charts/rag-app/values.yaml file, leave `config.truefoundry.apiKey/apiPrefix/existingSecret` under qdrant and truefoundry sections empty.
>
> If you don't keep it empty, you will get the error something like this:
>
> ```bash
> one or more objects failed to apply, reason: Deployment.apps "rag-qdrant-helm-app" is invalid: spec.template.spec.containers[0].env[4].valueFrom.secretKeyRef.name: Invalid value: "tfy-secret://tfy-eo:chintan-secrets:TFY-API-KEY": a lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character (e.g. 'example.com', regex used for validation is '[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*')
> ```

```bash
tfy apply -f deploy/rag-app.truefoundry.yaml
```

Or with `.env` expansion:

```bash
python deploy/apply_manifest.py deploy/rag-app.truefoundry.yaml
```

The app connects to Qdrant at `qdrant:6333` in the same namespace.

Alternatively, deploy both apps via the Python SDK after copying `.env.example` → `.env` and filling deploy vars (including `TFY_HOST`, `WORKSPACE_FQN`, `RAG_IMAGE`):

```bash
source .venv/bin/activate
python -m pip install -r deploy/requirements.txt
python deploy/deploy.py
```



### Step 3 — Deploy the RAG app Helm Chart via TrueFoundry UI

You can also deploy from the TrueFoundry UI: **New Deployment → Show Advanced → Helm → Select Workspace → Helm**:

- Qdrant: **Helm repository** → URL `https://qdrant.github.io/qdrant-helm`, chart `qdrant`, version `1.18.2`
- RAG app:
  - **Name**: Give app name of your preference
  - **Source helm repository**: GitHelmRepo
  - Git repository URL: `https://github.com/truefoundry/getting-started-examples.git` in this example
  - Revision: `chintan-rag-onboarding-with-helm` in this example
  - Path: `rag-onboarding-with-helm/charts/rag-app` in this example
  - Submit

After sometime, the RAG app will be in the **Running** and **Healthy** status.

Once you're done, remember to PAUSE the Helm Chart to reduce/avoid the unnecessary cost leakage. Best would be to DELETE it if not required in future.

Note: Helm Chart created from the private Git repo **can't be paused** (this is by design from the TrueFoundry platform). It will give this error: `Pausing a Helm application deployed from a Git source is not supported.` Hence, **do NOT forget to DELETE** it once you're done with it.

### Step 4 — Try it out locally

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

### Option B — Qdrant in Docker, RAG app from a virtual environment

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

Set `LOCAL_FAKE_LLM=false` and fill `TFY_API_KEY` / `TFY_HOST` / `TFY_LLM_GATEWAY_BASE_URL` in `.env` to use the real LLM Gateway.

## Configuration reference


| Variable                       | Example                                                        | Description                                            |
| ------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------ |
| `QDRANT_HOST` / `QDRANT_PORT`  | `qdrant` / `6333` (in-cluster) or `localhost` / `6333` (local) | Qdrant REST endpoint                                   |
| `QDRANT_API_KEY`               | *(empty)*                                                      | Optional Qdrant API key                                |
| `TFY_HOST`                     | `https://<your-org>.truefoundry.cloud`                         | Control plane URL (required if `TFY_API_KEY` is set)   |
| `TFY_API_KEY`                  | —                                                              | TrueFoundry API key for the LLM Gateway / SDK          |
| `TFY_LLM_GATEWAY_BASE_URL`     | `https://gateway.truefoundry.ai`                               | OpenAI-compatible base URL of the LLM Gateway          |
| `LOCAL_FAKE_LLM`               | `true` (local) / `false` (cluster)                             | Use local fake embeddings (no API key) for smoke tests |
| `LLM_MODEL`                    | `openai-main/gpt-4o-mini`                                      | Chat model ID on the gateway                           |
| `EMBEDDING_MODEL`              | `openai-main/text-embedding-3-small`                           | Embedding model ID                                     |
| `EMBEDDING_DIMENSIONS`         | `1536`                                                         | Vector size for Qdrant collection create               |
| `COLLECTION_NAME`              | `documents`                                                    | Qdrant collection name                                 |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200`                                                 | Text splitting parameters                              |
| `SIMILARITY_TOP_K`             | `5`                                                            | Number of chunks retrieved per query                   |
| `WORKSPACE_FQN`                | `<cluster>:<workspace>`                                        | Target workspace for `deploy.py`                       |
| `RAG_IMAGE`                    | `<registry>/rag-app:latest`                                    | Image used by `deploy.py`                              |


