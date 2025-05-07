import argparse
import logging
import os

from dotenv import load_dotenv
from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    Port,
    PythonBuild,
    Resources,
    Service,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)

service = Service(
    name="crewai-plot-agent",
    # --- Build configuration i.e. How to package and build source code ---
    # This will instruct TrueFoundry to automatically generate the Dockerfile and build it
    image=Build(
        build_spec=PythonBuild(
            command="python -m crewai_plot_agent.api",
            requirements_path="requirements.txt",
        )
        # You can use PythonBuild or DockerFileBuild for build spec like follows:
        # build_spec=PythonBuild() or build_spec=DockerFileBuild()
    ),
    # Alternatively, you can use an already built public image of this codebase like follows:
    # image=Image(image_uri="truefoundrycloud/emotion-classification-fastapi:0.0.1")
    # --- Endpoints configuration i.e. How requests will reach the container ---
    ports=[
        Port(
            port=8000,
            host="crewai-plot-agent-demo-8000.aws.demo.truefoundry.cloud",
        )
    ],
    # --- Environment Variables ---
    env={
        "CLICKHOUSE_HOST": os.getenv("CLICKHOUSE_HOST"),
        "CLICKHOUSE_PORT": os.getenv("CLICKHOUSE_PORT"),
        "CLICKHOUSE_USER": os.getenv("CLICKHOUSE_USER"),
        "CLICKHOUSE_PASSWORD": os.getenv("CLICKHOUSE_PASSWORD"),
        "CLICKHOUSE_DATABASE": os.getenv("CLICKHOUSE_DATABASE"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "MODEL": os.getenv("MODEL"),
    },
    # --- Resources ---
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=1000,
        ephemeral_storage_request=500,
        ephemeral_storage_limit=500,
    ),
    labels={
        "tfy_openapi_path": "openapi.json",
    },
)

# Get your workspace fqn from https://docs.truefoundry.com/docs/workspace#copy-workspace-fqn-fully-qualified-name
service.deploy(workspace_fqn="tfy-usea1-demo:demo")
