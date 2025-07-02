# getting-started-examples
Examples to get started with using TrueFoundry

Deployment
---
This example runs a simple mnist-classifaction job.
Mainly this example shows how to deploy to TrueFoundry using a Pythonfile and TrueFoundry Python SDK.

## Setup

> For setup, please refer to the following documentation:
> - [Create a ML Repo ](https://docs.truefoundry.com/docs/key-concepts#creating-an-ml-repo)
> - [Grant Editor access to ML Repo](https://docs.truefoundry.com/docs/key-concepts#grant-access-of-ml-repo-to-workspace)


## Run Locally

1. Install requirements

```shell
python -m pip install -r requirements.txt
```

2. Start the app

```shell
python train.py --num_epochs {{num_epochs}} --ml_repo {{ml_repo}}
```

## Deploy with TrueFoundry

1. Install `truefoundry`

```shell
python -m pip install -U "truefoundry>=0.10.0,<0.11.0"
```

2. Login

```shell
tfy login --host "<Host name of TrueFoundry UI. e.g. https://company.truefoundry.cloud>"
```

3. Deploy!

> Please refer to following docs
> - [Getting workspace FQN](https://docs.truefoundry.com/docs/key-concepts#get-workspace-fqn)

```shell
python deploy.py --workspace-fqn <Workspace FQN>
```
