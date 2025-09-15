#!/usr/bin/env python3
"""
Model Clone Script for TrueFoundry

This script clones a given model from one TrueFoundry's Repo and logs it to another TrueFoundry's Repo.
"""

import argparse
import os
import tempfile
import shutil

from truefoundry.ml import get_client, TransformersFramework

def main():
    """Main function to handle command line arguments and orchestrate the process."""
    parser = argparse.ArgumentParser(
        description="Clone a model from one TrueFoundry's Repo and log it to another TrueFoundry's Repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clone_model.py --source-ml-repo "wns-testing" --source-model-name "liquid-ai" --source-model-version "1" --target-ml-repo "wns-testing-dest" --target-model-name "liquid-ai"
        """
    )
    
    parser.add_argument(
        "--source-ml-repo",
        required=True,
        help="TrueFoundry source ML repository name"
    )

    parser.add_argument(
        "--source-model-name",
        required=True,
        help="TrueFoundry source model name"
    )

    parser.add_argument(
        "--source-model-version",
        required=True,
        help="TrueFoundry source model version"
    )
    
    parser.add_argument(
        "--target-ml-repo",
        required=True,
        help="TrueFoundry target ML repository name"
    )
    
    parser.add_argument(
        "--target-model-name",
        required=True,
        help="Name for the model in TrueFoundry target ML repository"
    )
    
    args = parser.parse_args()
    
    # Create temporary directory for download
    temp_dir = tempfile.mkdtemp()
    model_download_path = temp_dir
    
    try:

        client = get_client()

        print("List ML Repos:", client.list_ml_repos())

        source_model_version = client.get_model_version(
            ml_repo=args.source_ml_repo,
            name=args.source_model_name,
            version=args.source_model_version
        )

        download_info = source_model_version.download(path=model_download_path, overwrite=True)

        if os.path.exists(os.path.join(model_download_path, '.cache')):
            shutil.rmtree(os.path.join(model_download_path, '.cache'))

        print(f"Model downloaded to {model_download_path}")

        destination_model_version = client.log_model(
            ml_repo=args.target_ml_repo,
            name=args.target_model_name,
            description=source_model_version.description,
            metadata=source_model_version.metadata,
            model_file_or_folder=model_download_path,
            framework=source_model_version.framework,
        )
        
        print(f"\n✅ Success! Model logged to TrueFoundry with FQN: {source_model_version.fqn}")
        
        # Clean up temporary files
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
                    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        shutil.rmtree(temp_dir)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
