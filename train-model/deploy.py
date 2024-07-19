import argparse
import logging

from truefoundry.deploy import Build, Job, LocalSource, PythonBuild

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

# First we define how to build our code into a Docker image
image = Build(
    build_source=LocalSource(local_build=False),
    build_spec=PythonBuild(
        python_version="3.11",
        command="python train.py",
        requirements_path="requirements.txt",
    ),
)

job = Job(name="iris-train-job", image=image)
job.deploy(workspace_fqn=args.workspace, wait=False)
