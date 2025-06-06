# Deploying Custom Python function with MLflow

This example shows how to deploy a custom Python function with MLflow.

## Setup

```bash
pip install -r train/requirements.txt
```

## Log the model

```bash
python train/model.py
```

## Generate a Dockerfile

```bash
mlflow models generate-dockerfile -m models:/sentiment-model/1 --env-manager virtualenv --install-mlflow --output-directory .
```

## Deploy the model

```bash
python deploy.py --workspace-fqn ... --host ... --path ...
```

## Test the model

```bash
curl -X POST -H "Content-Type:application/json"  https://<endpoint>/invocations -d '{"inputs": [{"text": "hello"}]}'
```

You should see a response like this:

```json
{
  "predictions": [
    {
      "neg": 0,
      "neu": 1,
      "pos": 0,
      "compound": 0
    }
  ]
}
```
