import argparse
import logging

from servicefoundry import Build, Port, PythonBuild, Resources, Service

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
parser.add_argument("--path", type=str, required=False)
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
        "TFY_LLM_GATEWAY_HOST": "<Enter Truefoundry LLM Endpoint>",
        "TFY_API_KEY": "<Enter Truefoundry API key>",
        "MODEL_NAME": "<Enter model to be used from Truefoundry>",
    },
)
service.deploy(workspace_fqn=args.workspace_fqn)
