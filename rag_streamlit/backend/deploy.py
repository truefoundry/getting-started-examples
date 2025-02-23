import argparse
import logging

from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    Port,
    PythonBuild,
    Resources,
    Service,
)

logging.basicConfig(level=logging.INFO)

service = Service(
    name="demo-rag-api",
    # --- Build configuration i.e. How to package and build source code ---
    # This will instruct TrueFoundry to automatically generate the Dockerfile and build it
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
            host="ml.tfy-eo.truefoundry.cloud",
            path="/demo-rag-api-sai-ws-8000/",
        )
    ],
    # --- Environment Variables ---
    env={
        "ENVIRONMENT": "dev",
        "DEV_API_URL": "http://localhost:8000",
        "PROD_API_URL": "https://demo-rag-sai.tfy-usea1-ctl.devtest.truefoundry.tech/",
        "TFY_API_KEY": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImpJTkY3bXJ2RjA3cWJNUzllelhYeU5GYTBWVSJ9.eyJhdWQiOiI2OTZlNzQ2NS03MjZlLTYxNmMtM2EzOS02MTM4Mzg2NTYxNjEiLCJleHAiOjM2OTkzNDQ1MjgsImlhdCI6MTczOTc5MjUyOCwiaXNzIjoidHJ1ZWZvdW5kcnkuY29tIiwic3ViIjoiY203OHpqdWFyYnY1MzAxbDkxeG55OGVxaiIsImp0aSI6IjVjYjQyOTg2LTM4MjktNDYyYi04ZWEyLTM4YjlkMTBjNTg0MSIsInN1YmplY3RTbHVnIjoidGVzc3J0IiwidXNlcm5hbWUiOiJ0ZXNzcnQiLCJ1c2VyVHlwZSI6InNlcnZpY2VhY2NvdW50Iiwic3ViamVjdFR5cGUiOiJzZXJ2aWNlYWNjb3VudCIsInRlbmFudE5hbWUiOiJpbnRlcm5hbCIsInJvbGVzIjpbInRlbmFudC1tZW1iZXIiXSwiYXBwbGljYXRpb25JZCI6IjY5NmU3NDY1LTcyNmUtNjE2Yy0zYTM5LTYxMzgzODY1NjE2MSJ9.S8S3D4sDKxZJwJOSUBMEUd4x2AcQDbBlYI1IytGMBE6LJYO9Fk1raZ_j_SyicHKiMwcdCfmuLdjG3C7CGGmnfpP3tpLzv73KKYeV5vzpOqgmNG4b3WZjLdoeG6gVvcGF5PbVUYh51YC6nAw5NyGwGkwOD8R9EgtRgRhHmQr1teDCGEeZTkiFvZjbncdT9acoVr3ifAOq-CDUsV4pAsFUmsU50JhrFlsnjU-K8H24iWSQA9bdS1vConH7-c19ht0DWLXiizMj3Io_-K9EH4HYH4pkcx4QcOfGMxwNPpX5dMbSz7eMzhT21AOeWYNG5L0Xid-raMsyFdmeOaaNWMbHSg",
        "TFY_LLM_GATEWAY_BASE_URL": "https://llm-gateway.truefoundry.com/api/inference/openai",
        # QDRANT_API_URL=https://demo-rag-sai-qdrant.tfy-usea1-ctl.devtest.truefoundry.tech/
        "QDRANT_API_URL": "https://9d7ca1e5-9ef5-48bb-af88-16775d8af200.us-east4-0.gcp.cloud.qdrant.io",
        "QDRANT_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.OQqlajrayLt61kESpuVa997IoYbt42cpW35Xl70dIK8",
        "CHROMADB_API_URL": "https://demo-rag-sai-chroma-sai-k-ws.tfy-usea1-ctl.devtest.truefoundry.tech",
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
service.deploy(workspace_fqn="tfy-ea-dev-eo-az:sai-ws")
