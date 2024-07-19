import argparse
import logging

from truefoundry.deploy import Build, Port, PythonBuild, Resources, Service

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
parser.add_argument("--host", required=True, type=str)
args = parser.parse_args()

image = Build(
    build_spec=PythonBuild(
        command="locust -f benchmark.py",
        requirements_path="requirements.txt",
    )
)

service = Service(
    name="locust-llm-benchmark",
    image=image,
    resources=Resources(cpu_limit=1, cpu_request=1, memory_request=1500, memory_limit=2000),
    ports=[Port(port=8089, host=args.host)],
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
