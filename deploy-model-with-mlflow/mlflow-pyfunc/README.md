# Deploying a Hugging Face Model with MLflow and Transformers

This example shows how to deploy a Hugging Face model - a small language model - with MLflow and Transformers.

## Setup

```bash
pip install -r train/requirements.txt
```

## Log the model

```bash
python train/log_model.py
```

## Generate a Dockerfile

```bash
mlflow models generate-dockerfile -m models:/sentiment-model/1 --env-manager uv --install-mlflow --output-directory .
```

## Deploy the model

```bash
python deploy.py --workspace-fqn ... --host ... --path ...
```

## Test the model

```bash
curl -X POST https://<endpoint>/invocations -H 'Content-Type: application/json' -d '{"text": "I love this product!"}'
```

You should see a response like this:

```json

```
