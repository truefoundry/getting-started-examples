Deploy MNIST model with TorchServe

---

> [!tip]
> This example is deployed live [here](https://platform.live-demo.truefoundry.cloud/deployments/cmbltlrz6f87x01rj1z4k0o80?tab=pods)

> [!important]
> [TorchServe](https://github.com/pytorch/serve) is no longer being actively maintained. This example is just to demonstrate how to deploy any existing TorchServe apps.

This example was adapted from [TorchServe's Official MNIST Example](https://github.com/pytorch/serve/tree/62c4d6a1fdc1d071dbcf758ebd756029af20bd5e/examples/image_classifier/mnist).

### Install requirements

```shell
python -m pip install -r requirements.txt
```

### Package the model

```shell
torch-model-archiver --model-name mnist --version 1.0 --model-file mnist.py --serialized-file model/mnist_cnn.pt --handler mnist_handler.py
mkdir -p model_store/
mv mnist.mar model_store/
```

### Start the server

```shell
export MODEL_DIR="$(pwd)/model_store"
torchserve --foreground--model-store $MODEL_DIR --models all --ts-config config.properties --disable-token-auth --enable-model-api
```

### Example Inference Call

```bash
curl -X POST -H "Content-Type: application/json" --data @./example.json http://0.0.0.0:8080/v2/models/mnist/infer
```

You should see the following output:

```json
{
  "id": "d3b15cad-50a2-4eaf-80ce-8b0a428bd298",
  "model_name": "mnist",
  "model_version": "1.0",
  "outputs": [
    {
      "name": "input-0",
      "datatype": "INT64",
      "data": [
        1
      ],
      "shape": [
        1
      ]
    }
  ]
}
```
