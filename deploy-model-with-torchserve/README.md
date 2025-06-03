Deploy MNIST model with TorchServe
---

> [!important]
> [TorchServe](https://github.com/pytorch/serve) is no longer being actively maintained. This example is just to demonstrate how to deploy any existing TorchServe apps.

This example was adapted from [TorchServe's Official MNIST Example](https://github.com/pytorch/serve/tree/62c4d6a1fdc1d071dbcf758ebd756029af20bd5e/examples/image_classifier/mnist).

### Package the model

```shell
torch-model-archiver --model-name mnist --version 1.0 --model-file mnist.py --serialized-file model/mnist_cnn.pt --handler mnist_handler.py
mkdir -p model_store/
mv mnist.mar model_store/
```

### Deploy

```shell
 python deploy.py --workspace-fqn ... --host ... --path ...
```

### Example Inference


```
curl -X POST -H "Content-Type: application/json" --data @./example.json https://<endpoint>/v2/models/mnist/infer
```
