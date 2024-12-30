## Change the following variable value before deploying the workflow on your workspace

- Default value of `workspace_fqn` in main workflow function.
- Value of env variables `TFY_API_KEY` `TFY_HOST` in `task_config`.
- you can use virtual accout token as `TFY_API_KEY`, click [here](https://docs.truefoundry.com/docs/generating-truefoundry-api-keys#virtual-accounts) to learn about how to create virtual account.
- `host` value in `deploy.py`

## Deploying the workflow

You can deploy the workflow using the following command, make sure your truefoudry cli version is more thatn `4.0.0`.

```bash
tfy deploy workflow --name <wf-name> --file <file-name> --workspace-fqn <workspace-fqn>
```