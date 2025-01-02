## There are few pre-requisite we have fulfill before deploying the workflow

### Creating the ml repo and giving the workspace the access to that ml repo
- First create a ml repo where you want to log the models. To learn about how to create a ml repo, click [here](https://docs.truefoundry.com/docs/creating-a-ml-repo#/).
- Give ml repo access to the workspace where you will be deploying your workflow and the model. To know about how to give access click [here](https://docs.truefoundry.com/docs/key-concepts#/grant-access-of-ml-repo-to-workspace)

### Setting the value of default variables

- Set the value of env variables `TFY_API_KEY` `TFY_HOST` in `task_config` in `train-deploy-workflow.py` file.
- you can use virtual account token as `TFY_API_KEY`, click [here](https://docs.truefoundry.com/docs/generating-truefoundry-api-keys#virtual-accounts) to learn about how to create a virtual account.
- `host` value in `Port` field in `deploy.py` file

## Deploying the workflow

You can deploy the workflow using the following command, make sure your truefoudry cli version is more thatn `4.0.0`.

```bash
tfy deploy workflow --name <wf-name> --file train-deploy-workflow.py --workspace-fqn <workspace-fqn>
```
**Make sure you have workflow helm chart installed in the workspace in which you are deploying workflow**

## Executing the workflow
The workflow takes following arguments as input while executing the workflow.
`ml_repo`: The name of the ml repo where you want to deploy the model. The workspace should have access to this ml repo.
`workspace_fqn`: Workspace fqn where you want to deploy the model.
`epochs`: An array of integer which define the number of epoch you want to train the model for, each epoch will run with corresponding learning rate which you will give in `learning_rate` argument. The lenght of `epochs` and `learning_rate` shoud be same.
`learning_rate`: An array of float where each number is the learning rate you want your model to train with, corresponding to the epochs defined at same postion.
`accuracy_threshold`: The threshold value, so the workflow will deploy the model if its validation accuracy is greater than this threshold accuracy.