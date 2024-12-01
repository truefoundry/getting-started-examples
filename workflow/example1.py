from truefoundry.workflow import PythonTaskConfig, TaskPythonBuild, task, workflow


@task(
    task_config=PythonTaskConfig(
        image=TaskPythonBuild(
            python_version="3.9",
            pip_packages=["truefoundry[workflow]==0.3.0rc10"],
        ),
        service_account="<service-account>", # replace with your service account
    )
)
def say_hello() -> str:
    return "Hello, World!"


@workflow
def hello_world_wf() -> str:
    res = say_hello()
    return res
