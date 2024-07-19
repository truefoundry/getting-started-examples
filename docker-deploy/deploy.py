import argparse
import logging

from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    LocalSource,
    Port,
    Resources,
    Service,
)

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True, type=str, help="Name of the application.")
parser.add_argument(
    "--workspace_fqn",
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
args = parser.parse_args()

image = Build(
    build_source=LocalSource(local_build=False),
    build_spec=DockerFileBuild(),
)


service = Service(
    name=args.name,
    image=image,
    ports=[Port(port=8080, host=args.host)],
    resources=Resources(
        cpu_request=0.1,
        cpu_limit=0.1,
        memory_request=500,
        memory_limit=500,
    ),
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
