import argparse
import logging

from truefoundry.deploy import Build, LocalSource, Port, DockerFileBuild, Resources, Service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")


def str_or_none(value):
    return None if not value or value == "None" else value


parser = argparse.ArgumentParser()
parser.add_argument(
    "--name",
    required=False,
    default="mlflow-random-forest-svc",
    type=str,
    help="Name of the application.",
)
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
    name=args.name,
    # Define how to build your code into a Docker image
    image=Build(
        # `LocalSource` helps specify the details of your local source code.
        build_source=LocalSource(local_build=False),
        # `PythonBuild` helps specify the details of your Python Code.
        # These details will be used to templatize a DockerFile to build your Docker Image
        build_spec=DockerFileBuild(
            dockerfile_path="Dockerfile",
        ),
    ),
    # Set the ports your server will listen on
    ports=[
        # Providing a host and path value depends on the base domain urls configured in the cluster settings.
        # You can learn how to find the base domain urls available to you # Please see https://docs.truefoundry.com/docs/define-ports-and-domains#specifying-host
        Port(port=8080, host=args.host, path=args.path)
    ],
    # Define the resource constraints.
    #
    # Requests are the minimum amount of resources that a container needs to run.
    # Limits are the maximum amount of resources that a container can use.
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=1500,
    ),
    # Define environment variables that your Service will have access to
    env={
        "ENVIRONMENT": "dev",
        "MLSERVER_INFER_WORKERS": "1",
    },
    labels={"tfy_openapi_path": "/v2/docs/dataplane.json"},
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
