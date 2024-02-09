import logging, os, argparse
from servicefoundry import Build, Job, PythonBuild, Param, Port, LocalSource, Resources

# parsing the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--workspace_fqn", type=str, required=True, help="fqn of the workspace to deploy to"
)
args = parser.parse_args()

# defining the job specifications
job = Job(
    name="mnist-train-job",
    image=Build(
        build_spec=PythonBuild(
            command="python train.py --num_epochs {{num_epochs}} --ml_repo {{ml_repo}}",
            requirements_path="requirements.txt",
        ),
        build_source=LocalSource(local_build=False)
    ),
    params=[
            Param(name="num_epochs", default='4'),
            Param(name="ml_repo", param_type="ml_repo"),
        ],
    resources=Resources(
       cpu_request=0.5,
       cpu_limit=0.5,
       memory_request=1000,
       memory_limit=1500
    )
    
)
deployment = job.deploy(workspace_fqn=args.workspace_fqn)