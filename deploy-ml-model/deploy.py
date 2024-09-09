import argparse
import logging

from truefoundry.deploy import Build, LocalSource, Port, PythonBuild, Resources, Service

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=False, default="iris-classifier-svc", type=str, help="Name of the application.")
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
    type=str,
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
        build_spec=PythonBuild(
            python_version="3.11",
            command="uvicorn app:app --port 8000 --host 0.0.0.0",
            requirements_path="requirements.txt",
        ),
    ),
    # Set the ports your server will listen on
    ports=[
        # Providing a host and path value depends on the base domain urls configured in the cluster settings.
        # You can learn how to find the base domain urls available to you https://docs.truefoundry.com/docs/define-ports-and-domains#identifying-available-domains
        Port(port=8000, host=args.host, path=args.path)
    ],
    # Define the resource constraints.
    #
    # Requests are the minimum amount of resources that a container needs to run.
    # Limits are the maximum amount of resources that a container can use.
    resources=Resources(
        cpu_request=0.1,
        cpu_limit=0.1,
        memory_request=500,
        memory_limit=500,
    ),
    # Define environment variables that your Service will have access to
    env={"UVICORN_WEB_CONCURRENCY": "1", "ENVIRONMENT": "dev"},
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
