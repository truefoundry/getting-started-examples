import argparse
import logging

from truefoundry.deploy import (
    ArtifactsDownload,
    Build,
    LocalSource,
    Port,
    PythonBuild,
    Resources,
    Service,
    TruefoundryArtifactSource,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")


def str_or_none(value):
    return None if not value or value == "None" else value


parser = argparse.ArgumentParser()
parser.add_argument("--name", required=False, default="mnist-classifier", type=str, help="Name of the application.")
parser.add_argument(
    "--workspace_fqn",
    "--workspace-fqn",
    required=True,
    type=str,
    help="FQN of the workspace where application will be deployed",
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
parser.add_argument(
    "--model_version_fqn",
    required=True,
    type=str,
)
args = parser.parse_args()

service = Service(
    name="mnist-classification-svc",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="python gradio_demo.py",
            # for deploying fastapi
            # command="uvicorn fastapi_service:app --port 8000 --host 0.0.0.0",
            requirements_path="requirements.txt",
        ),
    ),
    ports=[Port(port=8000, host=args.host, path=args.path)],
    resources=Resources(
        memory_limit=500,
        memory_request=500,
        ephemeral_storage_limit=600,
        ephemeral_storage_request=600,
        cpu_limit=0.3,
        cpu_request=0.3,
    ),
    artifacts_download=ArtifactsDownload(
        artifacts=[
            TruefoundryArtifactSource(
                artifact_version_fqn=args.model_version_fqn,
                download_path_env_variable="MODEL_DOWNLOAD_PATH",
            )
        ]
    ),
    labels={"tfy_openapi_path": "openapi.json"},
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
