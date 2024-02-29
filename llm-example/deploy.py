import argparse
import logging

from servicefoundry import (
    ArtifactsDownload,
    Build,
    Port,
    PythonBuild,
    Resources,
    Service,
    TruefoundryArtifactSource,
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
parser.add_argument(
    "--llm_gateway_host",
    required=True,
    type=str,
    help="Host where the llm will be available for access.",
)
parser.add_argument("--path", type=str, required=False)
parser.add_argument(
    "--model_version_fqn",
    type=str,
    required=True,
    help="FQN of the model in mlrepo ",
)
parser.add_argument(
    "--llm_model",
    type=str,
    required=True,
    help="FQN of the artifact where model is present.",
)
args = parser.parse_args()

service = Service(
    name=args.name,
    image=Build(
        build_spec=PythonBuild(
            command="uvicorn app:app --port 8000 --host 0.0.0.0",
            requirements_path="requirements.txt",
        )
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
    env={
        "TFY_LLM_GATEWAY_HOST": args.llm_gateway_host,
        "LLM_MODEL": args.llm_model,
    },
    artifacts_download=ArtifactsDownload(
        artifacts=[
            TruefoundryArtifactSource(
                artifact_version_fqn=args.model_version_fqn,
                download_path_env_variable="CLASSIFIER_MODEL_PATH",
            )
        ]
    ),
)
service.deploy(workspace_fqn=args.workspace_fqn, wait=False)
