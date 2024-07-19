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

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", type=str, required=True)
parser.add_argument("--model_version_fqn", type=str, required=True)
parser.add_argument("--host", type=str, required=True)
parser.add_argument("--path", type=str, required=False)
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
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
