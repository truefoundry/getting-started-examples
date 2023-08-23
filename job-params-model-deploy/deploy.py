import argparse
import logging
import os
from servicefoundry import Build, PythonBuild, Resources, Job, Param, VolumeMount, LocalSource

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--workspace_fqn", type=str, required=True, help="fqn of the workspace to deploy to"
)
args = parser.parse_args()

# We now define our Service, we provide it a name, which script to run, environment variables and resources
job = Job(
    name="churn-prediction-train",
    image=Build(
        build_spec=PythonBuild(command="python main.py --n_neighbors {{n_neighbors}} --weights {{weights}}") ,
        build_source=LocalSource(local_build=False)
    ),
    env={
        "TFY_API_KEY": "paste api key here"
    },
    params=[
        Param(name="n_neighbors", default='5', description="Number of neighbors to use by default"),
        Param(name="weights", default='uniform', description="Weight function used in prediction.  Possible values: uniform, distance"),
    ],
    resources=Resources(
        cpu_request=1, cpu_limit=1, memory_request=2000, memory_limit=2000, ephemeral_storage_limit=2000, ephemeral_storage_request=1000,
    ),
)
# Finally, we call deploy to push it to Truefoundry platform
job.deploy(workspace_fqn=args.workspace_fqn)