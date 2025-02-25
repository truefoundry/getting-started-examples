# Retraining the workflow with Arize AI

In this example we will deploy a workflow and use arize ai to get the drift data and if drift is present then we will trigger the retraining workflow.

The retraining happens with following steps:

- First we will deploy the `train_model_workflow.py` workflow(see the below steps to deploy workflow)
- We will deploy a job which will run every two hours and will check if drift is present or not from arize ai and if drift is present then we will trigger the retraining workflow.
- After the worklflow is trained, the service will be deployed with name `bank-customer-churn-prediction` in same workfspace.

**Remember to deploy the workflow first and paste the application_fqn in `get_drift.py` file in get_drift_job director.**

## There are few pre-requisite we have fulfill before deploying the workflow

### Creating the ml repo and giving the workspace the access to that ml repo

- First create a ml repo where you want to log the models. To learn about how to create a ml repo, click [here](https://docs.truefoundry.com/docs/creating-a-ml-repo#/).
- Give ml repo access to the workspace where you will be deploying your workflow and the model. To know about how to give access click [here](https://docs.truefoundry.com/docs/key-concepts#/grant-access-of-ml-repo-to-workspace)

### Setting the value of default variables

- Set the value of env variables `TFY_API_KEY` `TFY_HOST` in `task_config` in `train_model_workflow.py` file.
- you can use virtual account token as `TFY_API_KEY`, click [here](https://docs.truefoundry.com/docs/generating-truefoundry-api-keys#virtual-accounts) to learn about how to create a virtual account.
- You have to set the values of `ARIZE_API_KEY`, `ARIZE_SPACE_ID` env variables in the `train_model_workflow.py` file to log the prediction data in the why labs to log the metrics for drift monitoring purpose.
- `host` value in `Port` field in `deploy.py` file
- `ARIZE_GRAPHQL_API_KEY` env variable in `get_drift_job/job.py`

## Running the workflow locally

To run the workflow locally, run the following command

- Update the `train_model_workflow.py` file and fill value of `ml_repo` and `workspace_fqn` field in the main function in the end of the file.
- Then run the below command to run the workflow locally.

```bash
python train-deploy-workflow.py
```

## Deploying the workflow

You can deploy the workflow using the following command, make sure your truefoudry cli version is more that `5.0.0`.

```bash
tfy deploy workflow --name <wf-name> --file train_model_workflow.py --workspace-fqn <workspace-fqn>
```

**Make sure you have workflow helm chart installed in the workspace in which you are deploying workflow**

## Executing the workflow

The workflow takes following arguments as input while executing the workflow.

- `ml_repo`: The name of the ml repo where you want to deploy the model. The workspace should have access to this ml repo.
- `workspace_fqn`: Workspace fqn where you want to deploy the model.

## Deploying the job

- Replace the `application fqn` in `get_drift.py` file.
- Replace the `workspace_fqn` in `job.py` file.
- Set the `ARIZE_GRAPHQL_API_KEY` env variable in `job.py`.
- Run the following command to deploy job

```
python job.py
```
