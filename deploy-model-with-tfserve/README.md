# Deploying MNIST model with TFServe
---

## (Optional) Train the model

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


## Deploy the model

```bash
python deploy.py --workspace-fqn ... --host ... --path ...
```

### Example Inference Call

```bash
curl -X POST -H "Content-Type: application/json" --data @./example.json https://<endpoint>/v1/models/mnist/versions/1:predict
```
