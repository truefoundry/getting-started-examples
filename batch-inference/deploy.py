import logging

from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    Image,
    Job,
    LocalSource,
    Param,
    PythonBuild,
    Resources,
)

logging.basicConfig(level=logging.INFO)

job = Job(
    name="text-class-batch-infer",
    # --- Build configuration i.e. How to package and build source code ---
    # This will instruct Truefoundry to automatically generate the Dockerfile and build it
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.11",
            requirements_path="requirements.txt",
            command="python batch_infer.py --input_bucket_name {{input_bucket_name}} --input_path {{input_path}} --output_bucket_name {{output_bucket_name}} --output_path {{output_path}} --batch_size {{batch_size}}",
        ),
        # Alternatively, you can also use DockerFileBuild to use the written Dockerfile like follows:
        # build_spec=DockerFileBuild()
    ),
    # Alternatively, you can use an already built image of this codebase like follows:
    # image=Image(image_uri="...")
    # --- Params configuration i.e. This allows triggering the job with custom parameters ---
    params=[
        Param(
            name="input_bucket_name",
            description="Name of the input bucket",
        ),
        Param(
            name="input_path",
            description="Path to the input data",
        ),
        Param(
            name="output_bucket_name",
            description="Name of the output bucket",
        ),
        Param(
            name="output_path",
            description="Path to the output data",
        ),
        Param(
            name="batch_size",
            description="Batch size for inference",
            default=4,
        ),
    ],
    # --- Environment Variables ---
    # Here we are using TrueFoundry Secrets to securely store the AWS credentials
    # You can also pass them directly as environment variables
    env={
        "AWS_ACCESS_KEY_ID": "tfy-secret://your-secret-group-name/AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "tfy-secret://your-secret-group-name/AWS_SECRET_ACCESS_KEY",
    },
    # Alternatively, you can also use a service account to access the buckets
    service_account=None,
    # --- Resources ---
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=4000,
        ephemeral_storage_request=10000,
        ephemeral_storage_limit=50000,
    ),
)

if __name__ == "__main__":
    # Get your workspace fqn from https://docs.truefoundry.com/docs/workspace#copy-workspace-fqn-fully-qualified-name
    job.deploy(workspace_fqn="<Enter Workspace FQN>")
