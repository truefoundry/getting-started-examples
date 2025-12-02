import logging
from truefoundry.deploy import (
    PythonBuild,
    LocalSource,
    Pip,
    Resources,
    Port,
    Service,
    NodeSelector,
    Build,
)

logging.basicConfig(level=logging.INFO)

service = Service(
    name="calculator-mcp",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            build_context_path="./",
            python_dependencies=Pip(requirements_path="requirements.txt"),
            command="python calculator.py",
        ),
    ),
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=1000,
        ephemeral_storage_request=500,
        ephemeral_storage_limit=500,
        node=NodeSelector(capacity_type="spot_fallback_on_demand"),
    ),
    env={
        "OAUTH_ISSUER": "https://truefoundry.okta.com/oauth2/sdfsafasd",
        "OAUTH_AUDIENCE": "https://calculator-mcp-server.example.com",
        "OAUTH_JWKS_URI": "https://example.okta.com/oauth2/sdfdsfasdfsdf/v1/keys",
    },
    ports=[
        Port(
            port=8000,
            protocol="TCP",
            expose=True,
            app_protocol="http",
            host="calculator-mcp-abhay-8000.tfy-usea1-ctl.devtest.truefoundry.tech",
        )
    ],
    workspace_fqn="tfy-usea1-devtest:abhay",
    replicas=1.0,
)


service.deploy(workspace_fqn="tfy-usea1-devtest:abhay", wait=False)
