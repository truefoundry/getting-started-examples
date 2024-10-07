Dockerfiled based Deployment
---
This example runs a simple Gradio app for inferring using a iris classifier.

Mainly this example shows how to deploy to TrueFoundry using a Dockerfile and TrueFoundry Python SDK.

## Run Locally

1. Install requirements

```shell
python -m pip install -r requirements.txt
```

2. Start the gradio app

```shell
python app.py
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

4. Deploy!

> Please refer to following docs
> - [Getting workspace FQN](https://docs.truefoundry.com/docs/key-concepts#getting-workspace-fqn)
> - [Get host and path for deploying applications](https://docs.truefoundry.com/docs/define-ports-and-domains#identifying-available-domains)

```shell
python deploy.py --name iris-gradio --workspace-fqn <Workspace FQN> --host <Ingress Host for the cluster> --path <optional path>
```

5. Trigger the deployed Job using the UI or Python SDK
https://docs.truefoundry.com/docs/triggering-a-job#trigger-a-job
