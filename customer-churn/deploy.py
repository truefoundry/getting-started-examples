import logging
import argparse

from truefoundry.deploy import Build, PythonBuild, LocalSource, Param, Resources, Job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")

parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", required=True, type=str)
args = parser.parse_args()

job = Job(
    name="churn-prediction-job",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="python main.py --n_neighbors {{n_neighbors}} --weights {{weights}} --ml_repo {{ml_repo}}",
            requirements_path="requirements.txt",
        ),
    ),
    params=[
        Param(
            name="n_neighbors",
            default=5,
            description="Number of neighbors to use by default",
        ),
        Param(
            name="weights",
            default="uniform",
            description="Weight function used in prediction. Possible values: uniform, distance",
        ),
        Param(
            name="ml_repo",
            param_type="ml_repo",
            description="ML Repo to log metrics and model to",
        ),
    ],
    resources=Resources(
        memory_limit=500,
        memory_request=500,
        ephemeral_storage_limit=600,
        ephemeral_storage_request=600,
        cpu_limit=0.3,
        cpu_request=0.3,
    ),
)

deployment = job.deploy(workspace_fqn=args.workspace_fqn, wait=False)