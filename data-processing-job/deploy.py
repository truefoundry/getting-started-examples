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
    name="pre-process-job",
    image=Build(
        build_spec=PythonBuild(
            command="python pre-process.py --dataset_usa {{dataset_usa}} --dataset_europe {{dataset_europe}} --ml_repo {{ml_repo}}",
            requirements_path="requirements.txt",
            python_version="3.8"

        ),
        build_source=LocalSource(local_build=False)
    ),
    params=[
            Param(name="dataset_usa", default="artifact:truefoundry/demo-repo/sales-data-usa:1"),
            Param(name="dataset_europe", default="artifact:truefoundry/demo-repo/sales-data-europe:1"),
            Param(name="ml_repo", param_type="ml_repo"),
        ],
    resources=Resources(
       cpu_request=0.1,
       cpu_limit=0.1,
       memory_request=500,
       memory_limit=1000
    )
    
)
deployment = job.deploy(workspace_fqn=args.workspace_fqn)