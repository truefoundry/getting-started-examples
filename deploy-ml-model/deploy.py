import argparse
import logging
from servicefoundry import Build, PythonBuild, Service, Resources, Port, ArtifactsDownload, ArtifactsCacheVolume, TruefoundryArtifactSource, LocalSource

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
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
    build_spec=PythonBuild(
        command="uvicorn app:app --port 8000 --host 0.0.0.0",
        requirements_path="requirements.txt",
    ),
    build_source=LocalSource(local_build=False)
)

service = Service(
    name="iris-model-deploy",
    image=image,
    ports=[Port(port=8000, host=args.host)],
    resources=Resources(
        cpu_request=0.1,
        cpu_limit=0.1,
        memory_request=500,
        memory_limit=500,
    ),
    env={"UVICORN_WEB_CONCURRENCY": "1", "ENVIRONMENT": "dev"},
    artifacts_download = ArtifactsDownload(
        artifacts = [
            TruefoundryArtifactSource(
                artifact_version_fqn="model:prodigaltech/test-ml-repo/logistic-regression:1",
                download_path_env_variable="MODEL_ID"
            )
        ],
        cache_volume=ArtifactsCacheVolume(
            storage_class="efs-sc",
            cache_size=1
        )

    ),
)
service.deploy(workspace_fqn=args.workspace_fqn)
