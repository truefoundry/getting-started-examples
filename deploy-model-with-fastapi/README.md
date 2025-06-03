# getting-started-examples
Examples to get started with using TrueFoundry

Deployment
---
This example runs a simple iris app for inferring using a iris classifier.
Mainly this example shows how to deploy to TrueFoundry using a Pythonfile and TrueFoundry Python SDK.

## Run Locally

1. Install requirements

```shell
python -m pip install -r requirements.txt
```

2. Start the iris app

```shell
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 server:app
```

## Deploy with TrueFoundry

1. Install `truefoundry`

```shell
python -m pip install -U "truefoundry>=0.9.2,<0.10.0"
```

2. Login

```shell
tfy login --host "<Host name of TrueFoundry UI. e.g. https://company.truefoundry.cloud>"
```

3. Deploy!

> Please refer to following docs
> - [Getting workspace FQN](https://docs.truefoundry.com/docs/key-concepts#get-workspace-fqn)
> - [Get host and path for deploying applications](https://docs.truefoundry.com/docs/define-ports-and-domains#identifying-available-domains)

```shell
python deploy.py --name iris --workspace-fqn <Workspace FQN> --host <Ingress Host for the cluster> --path <optional path>
```
