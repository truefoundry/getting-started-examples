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
mlflow models generate-dockerfile -m models:/qwen2.5-0.5b-instruct/1 --env-manager virtualenv --install-mlflow  --output-directory .
```

## Deploy the model

```bash
python deploy.py --workspace-fqn ... --host ... --path ...
```

## Test the model

```bash
curl -X POST https://<endpoint>/invocations -H 'Content-Type: application/json' -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

You should see a response like this:

```json
[{"id": "d8e85c94-677e-4061-80f3-2c92fcbb4af9", "object": "chat.completion", "created": 1749233134, "model": "Qwen/Qwen2.5-0.5B-Instruct", "usage": {"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40}, "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Hello! How can I assist you today?"}}]}]
```
