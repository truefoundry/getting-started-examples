import logging

from truefoundry.deploy import (
    Build,
    HealthProbe,
    HttpProbe,
    LocalSource,
    Port,
    PythonBuild,
    Resources,
    Service,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

service = Service(
    name="iris-class-svc",

    # --- Build configuration i.e. How to package and build source code ---
    # This will instruct TrueFoundry to automatically generate the Dockerfile and build it
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            requirements_path="requirements.txt",
            command="gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 server:app"
        )
    ),
    # --- Endpoints configuration i.e. How requests will reach the container ---
    ports=[
        Port(
            port=8000,
            # A model endpoint looks like https://{host}/{path}
            # Please see https://docs.truefoundry.com/docs/define-ports-and-domains#specifying-host
            host="iris-classifier.tfy-usea1-ctl.devtest.truefoundry.tech",
            path="/api/" # optional path for model endpoint,
        )
    ],

    # --- Environment Variables ---
    env={},

    # --- Resources ---
    resources=Resources(
        cpu_request=0.1,
        cpu_limit=0.5,
        memory_request=100,
        memory_limit=200,
        ephemeral_storage_request=100,
        ephemeral_storage_limit=500,
        # Uncomment the following line to add GPU resources
        # devices=[NvidiaGPU(type=GPUType.T4, count=1)]
    ),

    # --- Health Checks ---
    liveness_probe=HealthProbe(
        config=HttpProbe(path="/health", port=8000),
        initial_delay_seconds=3,
        period_seconds=5,
        timeout_seconds=2,
        success_threshold=1,
        failure_threshold=5
    ),

    readiness_probe=HealthProbe(
        config=HttpProbe(path="/health", port=8000),
        initial_delay_seconds=3,
        period_seconds=5,
        timeout_seconds=2,
        success_threshold=1,
        failure_threshold=3
    ),

    # --- Labels ---
    labels={
        "tfy_openapi_path": "openapi.json"
    }
)

# Get your workspace fqn from https://docs.truefoundry.com/docs/key-concepts#fqn
service.deploy(workspace_fqn="tfy-usea1-devtest:chirag-gpu-dev", wait=False)