import argparse
import logging

from truefoundry.deploy import Build, Job, PythonBuild

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

image = Build(
    build_spec=PythonBuild(
        command="locust -f benchmark.py",
        requirements_path="requirements.txt",
    )
)

job = Job(name="locust-llm-benchmark", image=image)
job.deploy(workspace_fqn=args.workspace_fqn)
