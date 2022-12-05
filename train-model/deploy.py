# Replace `<YOUR_WORKSPACE_FQN>` with the actual value.
import logging
from servicefoundry import Build, Job, PythonBuild

logging.basicConfig(level=logging.INFO)

# First we define how to build our code into a Docker image
image = Build(
    build_spec=PythonBuild(
        command="python train.py",
        requirements_path="requirements.txt",
    )
)
job = Job(
    name="iris-train-job",
    image=image
)
job.deploy(workspace_fqn = "tfy-ctl-euwe1-devtest:test123-ws")