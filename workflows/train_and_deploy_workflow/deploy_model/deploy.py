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


def deploy_service(model_version_fqn: str, workspace_fqn: str):
    service_name = "mnist-classification"
    service = Service(
        name=service_name,
        image=Build(
            build_source=LocalSource(local_build=False),
            build_spec=PythonBuild(
                python_version="3.11",
                command="python deploy_model/gradio_demo.py",
                # for deploying fastapi
                # command="uvicorn fastapi_service:app --port 8000 --host 0.0.0.0",
                requirements_path="deploy_model/requirements.txt",
            ),
        ),
        ports=[Port(port=8000, host=f"{service_name}-<your-host>")],
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
                    artifact_version_fqn=model_version_fqn,
                    download_path_env_variable="MODEL_DOWNLOAD_PATH",
                )
            ]
        ),
        labels={"tfy_openapi_path": "openapi.json"},
    )
    deployment = service.deploy(workspace_fqn=workspace_fqn, wait=False)
    return deployment.fqn
