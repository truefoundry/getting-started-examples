import argparse
import logging

from truefoundry.deploy import Build, Job, LocalSource, PythonBuild

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

job = Job(
    name="iris-train-job",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="python train.py",
            requirements_path="requirements.txt",
        ),
    ),
)
job.deploy(workspace_fqn=args.workspace_fqn, wait=False)
