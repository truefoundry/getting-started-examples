# getting-started-examples
Examples to get started with using TrueFoundry

Deployment
---
This example runs a simple mnist-classifaction Service.
Mainly this example shows how to deploy to TrueFoundry using a Pythonfile and TrueFoundry Python SDK.

## Run Locally

1. Install requirements -:

```shell
python -m pip install -r requirements.txt
```

2. Start the Deployment -:

(a). for gradio_demo
```shell
python gradio_demo.py
```

(b). for fastapi_serivce
```shell
uvicorn fastapi_service:app --port 8000 --host 0.0.0.0
```

## Deploy with TrueFoundry

1. Install `truefoundry`

```shell
python -m pip install -U "truefoundry>=0.4.1,<0.5.0"
```

2. Login

```shell
tfy login --host "<Host name of TrueFoundry UI. e.g. https://company.truefoundry.cloud>"
```

3. Deploy!

> Please refer to following docs
> - [Getting workspace FQN](https://docs.truefoundry.com/docs/key-concepts#getting-workspace-fqn)
> - [Get host and path for deploying applications](https://docs.truefoundry.com/docs/define-ports-and-domains#identifying-available-domains)

```shell
python deploy.py --name mnist-classifier --workspace-fqn <Workspace FQN> --host <Ingress Host for the cluster> --path <optional path> --model_version_fqn <Job Run details Models Tab>
```
