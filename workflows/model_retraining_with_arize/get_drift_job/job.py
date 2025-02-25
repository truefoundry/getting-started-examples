import argparse
import logging
import os

from truefoundry.deploy import Build, Job, LocalSource, PythonBuild, Schedule, ConcurrencyPolicy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)-8s %(message)s")

# parser = argparse.ArgumentParser()
# parser.add_argument("--service_url", required=True, type=str)
# args = parser.parse_args()

job = Job(
    name="get-drift-job",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            command="python get_drift.py",
            requirements_path="requirements.txt",
        ),
    ),
    env={
        "ARIZE_GRAPHQL_API_KEY": "<Your-arize-graphql-api-key>",
    },
    trigger=Schedule(
        schedule='0 */2 * * *',
        concurrency_policy=ConcurrencyPolicy.Forbid
    )
)
job.deploy(workspace_fqn="tfy-aws:dev-ws", wait=False)