import logging
import argparse

from truefoundry.deploy import Build, Job, LocalSource, Param, PythonBuild, Resources

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")

# parsing the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--workspace_fqn", type=str, required=True, help="fqn of the workspace to deploy to")
args = parser.parse_args()

# defining the job specifications
job = Job(
    name="mnist-train-job",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="python train.py --num_epochs {{num_epochs}} --ml_repo {{ml_repo}}",
            requirements_path="requirements.txt",
        ),
    ),
    params=[
        Param(name="num_epochs", default="4"),
        Param(name="ml_repo", param_type="ml_repo"),
    ],
    resources=Resources(cpu_request=0.5, cpu_limit=0.5, memory_request=1500, memory_limit=2000),
)
deployment = job.deploy(workspace_fqn=args.workspace_fqn, wait=False)
