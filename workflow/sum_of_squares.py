from truefoundry.workflow import task, workflow, PythonTaskConfig, TaskPythonBuild
from truefoundry.deploy import Resources


cpu_task_config = PythonTaskConfig(
    image=TaskPythonBuild(
        python_version="3.9",
        pip_packages=["truefoundry[workflow]==0.3.0rc10"],
    ),
    resources=Resources(cpu_request=0.45),
    service_account="<service-account>", # replace with your service account
)

# Task 1: Generate a list of numbers
@task(task_config=cpu_task_config)
def generate_numbers(n: int) -> list[int]:
    return list(range(1, n + 1))

# Task 2: Calculate the square of each number in the list
@task(task_config=cpu_task_config)
def square_numbers(numbers: list[int]) -> list[int]:
    return [x ** 2 for x in numbers]

# Task 3: Sum the squared numbers
@task(task_config=cpu_task_config)
def sum_squares(squared_numbers: list[int]) -> int:
    return sum(squared_numbers)

# Workflow: Orchestrate the tasks
@workflow
def simple_pipeline(n: int) -> int:
    numbers = generate_numbers(n=n)
    squared_numbers = square_numbers(numbers=numbers)
    result = sum_squares(squared_numbers=squared_numbers)
    return result

# Runs the pipeline locally
if __name__ == "__main__":
    result = simple_pipeline(n=5)
    print(f"The sum of squares from 1 to 5 is: {result}")
