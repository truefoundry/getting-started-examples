import argparse
import logging
from servicefoundry import Build, Job, PythonBuild, Param, LocalSource

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

# First we define how to build our code into a Docker image
image = Build(
    build_spec=PythonBuild(
        command="python train.py --artifact_version_fqn {{artifact_version_fqn}} --ml_repo_name {{ml_repo_name}}",
        requirements_path="requirements.txt",
    ),
    build_source=LocalSource(local_build=False)
)

job = Job(
    name="iris-train-job",
    image=image,
    params=[
        Param(name="ml_repo_name", param_type="ml_repo"),
        Param(name="artifact_version_fqn"), 
    ],
)
job.deploy(workspace_fqn=args.workspace_fqn)