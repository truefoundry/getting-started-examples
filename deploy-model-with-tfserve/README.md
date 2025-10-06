# Deploying MNIST model with TFServe

---

> [!tip]
> This example is deployed live [here](https://platform.live-demo.truefoundry.cloud/deployments/cmbltl1g1f86m01rj09pf110i?tab=pods)

### (Optional) Train the model

```bash
pip install -r requirements.txt
python train.py
```

You can inspect the model signature using the following command:

```bash
saved_model_cli show --dir models/mnist/1/ --tag_set serve --signature_def serving_default
```

which gives us

```
The given SavedModel SignatureDef contains the following input(s):
  inputs['keras_tensor'] tensor_info:
      dtype: DT_FLOAT
      shape: (-1, 28, 28, 1)
      name: serving_default_keras_tensor:0
The given SavedModel SignatureDef contains the following output(s):
  outputs['output_0'] tensor_info:
      dtype: DT_FLOAT
      shape: (-1, 10)
      name: StatefulPartitionedCall_1:0
Method name is: tensorflow/serving/predict
```

### Start the server

```bash
export MODEL_DIR="$(pwd)/models/mnist"
tensorflow_model_server --model_name=mnist --model_base_path=$MODEL_DIR --enable_batching --batching_parameters_file=./batching.config --rest_api_port=8000 --rest_api_timeout_in_ms=10000 --enable_model_warmup
```

### Example Inference Call

```bash
curl -X POST -H "Content-Type: application/json" --data @./example.json http://0.0.0.0:8000/v1/models/mnist/versions/1:predict
```
