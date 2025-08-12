Batch Inference Text Classification
---
This example runs batch inference as a Job.

- Downloads Data from S3
- Downloads the model from HuggingFace Hub
- Runs batch inference
- Uploads the results to S3

## Run Locally

1. Install requirements

```shell
python -m pip install -r requirements.txt
```

1. Run locally without S3 interaction

```shell
python batch_infer.py \
    --local \
    --input_bucket_name dummy \
    --input_path ./sample.csv \
    --output_bucket_name dummy \
    --output_path sample.out.csv
```

## Deploy with TrueFoundry

1. Install `truefoundry`

```shell
python -m pip install -U "truefoundry>=0.11.0,<0.12.0"
```

2. Login

```shell
tfy login --host "<Host name of TrueFoundry UI. e.g. https://company.truefoundry.cloud>"
```

3. Edit `env` section in `deploy.py` to link your S3 credential secrets

```python
# --- Environment Variables ---
# Here we are using TrueFoundry Secrets to securely store the AWS credentials
# You can also pass them directly as environment variables
env={
    "AWS_ACCESS_KEY_ID": "tfy-secret://your-secret-group-name/AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY": "tfy-secret://your-secret-group-name/AWS_SECRET_ACCESS_KEY",
},
```

4. Deploy!

> Please refer to following docs
> - [Getting workspace FQN](https://docs.truefoundry.com/docs/key-concepts#get-workspace-fqn)

```shell
python deploy.py --workspace_fqn <Workspace FQN>
```

5. Trigger the deployed Job using the UI or Python SDK
https://docs.truefoundry.com/docs/triggering-a-job#trigger-a-job
