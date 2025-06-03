# Deploy MNIST Model with MMS
---

### Package the model

```bash
model-archiver --model-name mnist --model-path model/ --handler mnist_handler.py:handle --export-path model_store/ --runtime python --force
```

### Deploy

```shell
python deploy.py --workspace-fqn ... --host ... --path ...
```

### Example Inference Call

```bash
curl -X POST -H "Content-Type: application/json" https://<endpoint>/predictions/mnist -T 0.png
```
