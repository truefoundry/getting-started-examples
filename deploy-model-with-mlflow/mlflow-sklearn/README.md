# Deploy Sklearn Model with MLflow and MLServer

---

> [!tip]
> This example is deployed live [here](https://platform.live-demo.truefoundry.cloud/deployments/cmbltc3pof7gi01rjer0u7qi6?tab=pods)

## Setup

```bash
pip install -r train/requirements.txt
```

## Train Model

```bash
python train/train_and_log_model.py
```

## Generate Dockerfile

```bash
mlflow models generate-dockerfile -m models:/sk-learn-random-forest-reg-model/1 --env-manager virtualenv --install-mlflow --enable-mlserver  --output-directory .
```

## Deploy Model

```bash
python deploy.py --workspace-fqn ... --host ... --path ...
```

## Test Model

```bash
curl -X POST -H "Content-Type:application/json"  https://<endpoint>/v2/models/sk-learn-random-forest-reg-model/infer -d @./example-input.json
```

You should see the output like this:

```json
{
  "model_name": "sk-learn-random-forest-reg-model",
  "model_version": "1",
  "id": "d2b0e566-5be1-4eea-99e8-88bd55d50b20",
  "parameters": {
    "content_type": "np"
  },
  "outputs": [
    {
      "name": "output-1",
      "shape": [
        2,
        1
      ],
      "datatype": "FP64",
      "parameters": {
        "content_type": "np"
      },
      "data": [
        68.8466918640391,
        68.49980732030235
      ]
    }
  ]
}
```
