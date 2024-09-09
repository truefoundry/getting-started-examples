import argparse
import logging

from truefoundry.deploy import Build, LocalSource, Port, PythonBuild, Resources, Service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")


def str_or_none(value):
    return None if not value or value == "None" else value


parser = argparse.ArgumentParser()
parser.add_argument(
    "--workspace_fqn",
    "--workspace-fqn",
    required=True,
    type=str,
    help="FQN of the workspace where application will be deployed.",
)
parser.add_argument(
    "--host",
    required=True,
    type=str,
    help="Host where the application will be available for access. Ex:- my-app.my-org.com",
)
parser.add_argument(
    "--path",
    required=False,
    default=None,
    type=str_or_none,
    help="Path in addition to the host where the application will be available for access. Eg: my-org.com/my-path",
)
args = parser.parse_args()

service = Service(
    name="locust-llm-benchmark",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="locust -f benchmark.py",
            requirements_path="requirements.txt",
        ),
    ),
    resources=Resources(cpu_limit=1, cpu_request=1, memory_request=1500, memory_limit=2000),
    ports=[Port(port=8089, host=args.host)],
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
