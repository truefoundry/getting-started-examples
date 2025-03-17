import argparse
import logging
from truefoundry.deploy import Service, Build, DockerFileBuild, PythonBuild, Port, Resources
from dotenv import load_dotenv
import os
load_dotenv()

logging.basicConfig(level=logging.INFO)

service = Service(
  name="crewai-streamlit",

  # --- Build configuration i.e. How to package and build source code ---
  # This will instruct TrueFoundry to automatically generate the Dockerfile and build it
  image=Build(
    build_spec=PythonBuild(
      command="streamlit run src/crewai_plot_agent/app.py",
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
      port=8501,
      host="crewai-streamlit-demo-8501.aws.demo.truefoundry.cloud",
    )
  ],

  # --- Environment Variables ---
  env={
    "API_BASE_URL": os.getenv("API_BASE_URL"),
  },

  # --- Resources ---
  resources=Resources(
    cpu_request=0.5, cpu_limit=0.5,
    memory_request=1000, memory_limit=1000,
    ephemeral_storage_request=500, ephemeral_storage_limit=500
  ),

  labels={
    "tfy_openapi_path": "openapi.json",
  },
)

# Get your workspace fqn from https://docs.truefoundry.com/docs/workspace#copy-workspace-fqn-fully-qualified-name
service.deploy(workspace_fqn="tfy-usea1-demo:demo")