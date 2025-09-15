#!/usr/bin/env python3
"""
Model Clone Script for TrueFoundry

This script clones a given model from one TrueFoundry's Repo and logs it to another TrueFoundry's Repo.
"""

import argparse
import os
import tempfile
import shutil
import time

from truefoundry.ml import get_client, TransformersFramework

def main():
    
    print("Starting model cloning process...")

    """Main function to handle cloning a model from one TrueFoundry's Repo and logging it to another TrueFoundry's Repo"""

    parser = argparse.ArgumentParser(
        description="Clone a model from one TrueFoundry's Repo and log it to another TrueFoundry's Repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python clone_model.py --source-model-fqn=model:truefoundry/wns-testing/liquid-ai:1 --target-ml-repo=wns-testing-dest
        """
    )
    
    parser.add_argument(
        "--source-model-fqn",
        required=True,
        help="TrueFoundry source model FQN"
    )

    parser.add_argument(
        "--target-ml-repo",
        required=True,
        help="TrueFoundry target ML repository name"
    )
    MAX_RETRIES = os.getenv("MAX_RETRIES", 5)
    INITIAL_BACKOFF_SECONDS = os.getenv("INITIAL_BACKOFF_SECONDS", 2)
    
    args = parser.parse_args()
    
    # Create temporary directory for download
    temp_dir = tempfile.mkdtemp()
    model_download_path = temp_dir
    
    try:
        client = get_client()
        print(f"Successfully connected to TrueFoundry")

        print(f"Getting source model version for FQN: {args.source_model_fqn}")
        source_model_version = client.get_model_version_by_fqn(
            fqn=args.source_model_fqn
        )

        ml_repos = client.list_ml_repos()
        if args.target_ml_repo not in ml_repos:
            raise ValueError(f"ML Repo {args.target_ml_repo} not found")

        print(f"Downloading model to {model_download_path}")

        run_with_retry(
            source_model_version.download,
            max_retries=MAX_RETRIES,
            initial_backoff=INITIAL_BACKOFF_SECONDS,
            path=model_download_path,
            overwrite=True
        )    

        if os.path.exists(os.path.join(model_download_path, '.cache')):
            shutil.rmtree(os.path.join(model_download_path, '.cache'))

        print(f"Model downloaded successfully to {model_download_path}")
        source_model_version.metadata["source_model_fqn"] = args.source_model_fqn

        print(f"Uploading model to {args.target_ml_repo}")

        destination_model_version = run_with_retry(
            client.log_model,
            max_retries=MAX_RETRIES,
            initial_backoff=INITIAL_BACKOFF_SECONDS,
            ml_repo=args.target_ml_repo,
            name=source_model_version.name,
            description=source_model_version.description,
            metadata=source_model_version.metadata,
            model_file_or_folder=model_download_path,
            framework=source_model_version.framework,
        )
        
        print(f"\n✅ Success! Model logged to TrueFoundry with FQN: {destination_model_version.fqn}")
        
        # Clean up temporary files
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
                    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        shutil.rmtree(temp_dir)
        return 1

    return 0

def run_with_retry(func, max_retries, initial_backoff, *args, **kwargs):
    """
    Runs a function with an exponential backoff retry mechanism.

    :param func: The function to execute.
    :param max_retries: Maximum number of times to retry.
    :param initial_backoff: The initial wait time in seconds for the first retry.
    :param args: Positional arguments to pass to the function.
    :param kwargs: Keyword arguments to pass to the function.
    :return: The result of the function if successful.
    :raises Exception: If the function fails after all retries.
    """
    backoff = initial_backoff
    for attempt in range(max_retries + 1):
        try:
            # First attempt (attempt == 0) is without a wait.
            if attempt > 0:
                print(f"Retrying in {backoff:.2f} seconds...")
                time.sleep(backoff)
                backoff *= 2  # Exponentially increase backoff time

            return func(*args, **kwargs)

        except Exception as e:
            if attempt + 1 > max_retries:
                print(f"Final attempt failed. Reached max retries ({max_retries}).")
                raise e  # Re-raise the last exception
            else:
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying..."
                )

if __name__ == "__main__":
    exit(main())
