#!/usr/bin/env python3
"""
Hugging Face Model Import Script for TrueFoundry

This script downloads a Hugging Face model from a given URL and logs it to TrueFoundry's model registry.
"""

import argparse
import os
import tempfile
import shutil

from huggingface_hub import snapshot_download
from truefoundry.ml import get_client, TransformersFramework

def main():
    """Main function to handle command line arguments and orchestrate the process."""
    parser = argparse.ArgumentParser(
        description="Download a Hugging Face model and log it to TrueFoundry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --model-id "microsoft/DialoGPT-medium" --ml-repo "my-ml-repo" --model-name "dialogpt-medium" --model-type "text-generation"
  python main.py --model-id "gpt2" --ml-repo "my-repo" --model-name "gpt2-model" --model-type "text-generation"
  python main.py --model-id "LiquidAI/LFM2-350M" --ml-repo "wns-testing" --model-name "liquid-ai" --model-type "text-generation" 
        """
    )
    
    parser.add_argument(
        "--model-id",
        required=True,
        help="Hugging Face model ID (e.g., 'microsoft/DialoGPT-medium')"
    )
    
    parser.add_argument(
        "--ml-repo",
        required=True,
        help="TrueFoundry ML repository name"
    )
    
    parser.add_argument(
        "--model-name",
        required=True,
        help="Name for the model in TrueFoundry"
    )

    parser.add_argument(
        "--model-type",
        required=True,
        help="Type of the model (e.g., 'text-generation')"
    )
    
    parser.add_argument(
        "--hf-token",
        required=False,
        help="Hugging Face token for private models"
    )
    
    args = parser.parse_args()
    
    # Create temporary directory for download
    temp_dir = tempfile.mkdtemp()
    model_download_path = temp_dir
    
    try:

        snapshot_download(
            args.model_id,
            revision=None,
            cache_dir=None,
            local_dir=model_download_path,
            ignore_patterns=["*.h5", "*.ot"],
            local_dir_use_symlinks=False,
            token=args.hf_token,
        )

        if os.path.exists(os.path.join(model_download_path, '.cache')):
            shutil.rmtree(os.path.join(model_download_path, '.cache'))

        print(f"Model downloaded to {model_download_path}")
        ML_REPO = args.ml_repo         # ML Repo to upload to
        MODEL_NAME = args.model_name  # Model Name to upload as

        client = get_client()
        model_version = client.log_model(
            ml_repo=ML_REPO,
            name=MODEL_NAME,
            model_file_or_folder=model_download_path,
            framework=TransformersFramework(
                model_id=args.model_id,
                pipeline_tag=args.model_type
            ),
        )
        
        print(f"\n✅ Success! Model logged to TrueFoundry with FQN: {model_version.fqn}")
        
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
