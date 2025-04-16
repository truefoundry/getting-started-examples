import logging

from truefoundry.deploy import Build, DockerFileBuild, Port, Resources, Service

logging.basicConfig(level=logging.INFO)

service = Service(
    name="demo-rag-api",
    # --- Build configuration i.e. How to package and build source code ---
    # This will instruct TrueFoundry to generate the Dockerfile and build it automatically
    image=Build(
        build_spec=DockerFileBuild(
            dockerfile_path="./Dockerfile",
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
            host="ml.example.truefoundry.cloud",
            path="path",
        )
    ],
    # --- Environment Variables ---
    env={
        "ENVIRONMENT": "dev",
        "DEV_API_URL": "http://localhost:8000",
        "PROD_API_URL": "PROD_API_URL",
        "TFY_API_KEY": "TFY_API_KEY",
        "TFY_LLM_GATEWAY_BASE_URL": "TFY_LLM_GATEWAY_BASE_URL",
        # QDRANT_API_URL=https://demo-rag-sai-qdrant.tfy-usea1-ctl.devtest.truefoundry.tech/
        "QDRANT_API_URL": "QDRANT_API_URL",
        "QDRANT_API_KEY": "QDRANT_API_KEY",
        "QDRANT_API_PORT": 443,
        "QDRANT_API_PREFIX": "QDRANT_API_PREFIX",
        "CHROMADB_API_URL": "CHROMADB_API_URL",
    },
    # --- Resources ---
    resources=Resources(
        cpu_request=1,
        cpu_limit=2,
        memory_request=2000,
        memory_limit=4000,
        ephemeral_storage_request=1000,
        ephemeral_storage_limit=2000,
    ),
    labels={
        "tfy_openapi_path": "openapi.json",
    },
)

# Get your workspace fqn from https://docs.truefoundry.com/docs/workspace#copy-workspace-fqn-fully-qualified-name
service.deploy(workspace_fqn="cluster:your-ws")
