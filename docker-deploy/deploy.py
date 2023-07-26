import argparse
import logging
from servicefoundry import Build, PythonBuild, Service, Resources, Port

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
parser.add_argument("--host", required=True, type=str)
args = parser.parse_args()

image = Build(
    build_spec=PythonBuild(
        command="uvicorn app:app --port 8000 --host 0.0.0.0",
        requirements_path="requirements.txt"
    )
)

service = Service(
    name="ml-deploy",
    image=image,
    ports=[
        Port(
            port=8000,
            host=args.host,
        )
    ],
    resources=Resources(
      memory_limit=500,
      memory_request=500,
      ephemeral_storage_limit=600,
      ephemeral_storage_request=600,
      cpu_limit=0.3,
      cpu_request=0.3
    ),
    env={
        "UVICORN_WEB_CONCURRENCY": "1",
        "ENVIRONMENT": "dev"
    }
)
service.deploy(workspace_fqn=args.workspace)