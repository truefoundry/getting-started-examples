import logging
from servicefoundry import Build, PythonBuild, Service, Resources

logging.basicConfig(level=logging.INFO)

image = Build(
    build_spec=PythonBuild(
        command="uvicorn app:app --port 8000 --host 0.0.0.0",
        requirements_path="requirements.txt"
    )
)

service = Service(
    name="ml-deploy",
    image=image,
    ports=[{"port": 8000}],
    resources=Resources(memory_limit=1500, memory_request=1000),
    env={
        "UVICORN_WEB_CONCURRENCY": "1",
        "ENVIRONMENT": "dev"
    }
)
service.deploy(workspace_fqn="tfy-ctl-euwe1-devtest:test123-ws")
