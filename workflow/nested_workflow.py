from truefoundry.workflow import conditional, task, workflow, PythonTaskConfig, TaskPythonBuild
from truefoundry.deploy import Resources


cpu_task_config = PythonTaskConfig(
    image=TaskPythonBuild(
        python_version="3.9",
        pip_packages=["truefoundry[workflow]==0.3.0rc10"],
    ),
    resources=Resources(cpu_request=0.45),
    service_account="<service-account>", # replace with your service account
)


@task(task_config=cpu_task_config)
def calculate_circle_circumference(radius: float) -> float:
    return 2 * 3.14 * radius  # Task to calculate the circumference of a circle


@task(task_config=cpu_task_config)
def calculate_circle_area(radius: float) -> float:
    return 3.14 * radius * radius  # Task to calculate the area of a circle


@workflow
def nested_conditions(radius: float) -> float:
    return (
        conditional("nested_conditions")
        .if_((radius >= 0.1) & (radius < 1.0))
        .then(
            conditional("inner_nested_conditions")
            .if_(radius < 0.5)
            .then(calculate_circle_circumference(radius=radius))
            .elif_((radius >= 0.5) & (radius < 0.9))
            .then(calculate_circle_area(radius=radius))
            .else_()
            .fail("0.9 is an outlier.")
        )
        .elif_((radius >= 1.0) & (radius <= 10.0))
        .then(calculate_circle_area(radius=radius))
        .else_()
        .fail("The input must be within the range of 0 to 10.")
    )


if __name__ == "__main__":
    print(f"nested_conditions(0.4): {nested_conditions(radius=0.4)}")