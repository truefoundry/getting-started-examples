# Deploy Scikit-Learn Iris flower classification model with FastAPI

---

> [!tip]
> This example is deployed live [here](https://platform.live-demo.truefoundry.cloud/deployments/cm4qm5p0k8p8001rm24utckn0?tab=pods)

### Install requirements

1. Install requirements

```shell
python -m pip install -r requirements.txt
```

### Start the server

```shell
export MODEL_DIR="$(pwd)"
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 server:app
```

### Example Inference Call

```shell
curl -X 'POST' \
  'http://0.0.0.0:8000/predict?sepal_length=1&sepal_width=1&petal_length=1&petal_width=1' \
  -H 'accept: application/json'
```
