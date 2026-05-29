import logging
from truefoundry.deploy import (
    Param,
    Manual,
    Build,
    Resources,
    Job,
    PythonBuild,
    NodeSelector,
    LocalSource,
)
import argparse

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

job = Job(
    name="hf-model-importer",
    image=Build(
        # Set build_source=LocalSource(local_build=False), in order to deploy code from your local.
        # With local_build=False flag, docker image will be built on cloud instead of local
        # Else it will try to use docker installed on your local machine to build the image
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            build_context_path="./hf-model-import-job",
            requirements_path="requirements.txt",
            command="python main.py --model-id {{model_id}} --model-type {{model_type}} --ml-repo {{ml_repo}} --model-name {{model_name}}",
        ),
    ),
    trigger=Manual(),
    params=[
        Param(
            name="model_id", description="Hugging face model ID", param_type="string"
        ),
        Param(
            name="model_type",
            description="model type from hugging face",
            default="text-generation",
            param_type="string",
        ),
        Param(
            name="ml_repo",
            description="ML repo name to import model to",
            param_type="ml_repo",
        ),
        Param(
            name="model_name",
            description="Model name in truefoundry model registry",
            param_type="string",
        ),
    ],
    resources=Resources(
        cpu_request=1.0,
        cpu_limit=2.0,
        memory_request=2000,
        memory_limit=4000,
        ephemeral_storage_request=10000,
        ephemeral_storage_limit=20000,
    ),
    retries=0,
    workspace_fqn=args.workspace_fqn,
)


job.deploy(workspace_fqn=args.workspace_fqn, wait=False)
