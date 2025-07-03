# Deploy MNIST Model with MMS

---

### Install requirements

```bash
python -m pip install -r requirements.txt
```

### Package the model

```bash
model-archiver --model-name mnist --model-path model/ --handler mnist_handler.py:handle --export-path model_store/ --runtime python --force
```

### Start the server

```bash
export MODEL_DIR="$(pwd)/model_store"
multi-model-server --foreground --model-store $MODEL_DIR --start --mms-config config.properties
```

### Example Inference Call

```bash
curl -X POST -H "Content-Type: application/json" http://0.0.0.0:8080/predictions/mnist -T 0.png
```
