import argparse
import json
import logging
import os
import sys
import tempfile
from typing import Optional

import boto3
import torch
from datasets import load_dataset
from transformers import pipeline
from transformers.modeling_utils import tempfile

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:    %(asctime)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)


_MODEL = None


def get_model():
    """
    Loads the model from Huggingface Hub
    Caches it in Python Module's globals

    You can also load the model from other sources like S3, TrueFoundry Artifacts

    For TrueFoundry Artifacts: https://docs.truefoundry.com/docs/log-models#get-model-version-and-download
    """
    global _MODEL
    if _MODEL is None:
        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Loading model on device {device}")
        _MODEL = pipeline(
            "text-classification",
            model="bhadresh-savani/albert-base-v2-emotion",
            device=device,
        )
    return _MODEL


def download_input_files(workdir: str, input_bucket_name: str, input_path: str):
    """
    Downloads the input data from S3

    You can also load the model from other sources like TrueFoundry Artifacts

    For TrueFoundry DataDirectory: https://docs.truefoundry.com/docs/log-and-get-data#downloading-data-from-the-data-directory
    For TrueFoundry Artifacts: https://docs.truefoundry.com/docs/log-artifacts#get-the-artifact-version-and-download-contents
    """
    logger.info(f"Downloading input files from S3, Bucket: {input_bucket_name}, Path: {input_path}")
    input_filepath = os.path.join(workdir, "input.csv")
    s3_client = boto3.client("s3")
    s3_client.download_file(Bucket=input_bucket_name, Key=input_path, Filename=input_filepath)
    return input_filepath


def upload_output_files(output_filepath: str, output_bucket_name: str, output_path: str):
    """
    Uploads the output data to S3

    You can also upload the model to other sources like TrueFoundry Artifacts, Data Directories

    For TrueFoundry DataDirectory: https://docs.truefoundry.com/docs/log-and-get-data#logging-data-in-a-data-directory
    For TrueFoundry Artifacts: https://docs.truefoundry.com/docs/log-artifacts#python-sdk
    """
    logger.info(f"Uploading output files to S3, Bucket: {output_bucket_name}, Path: {output_path}")
    s3_client = boto3.client("s3")
    s3_client.upload_file(Bucket=output_bucket_name, Key=output_path, Filename=output_filepath)


def infer(batch):
    """
    Inference function that takes a batch of data and returns the predictions
    """
    model = get_model()
    predictions = model(batch["text"], top_k=None, batch_size=len(batch))
    return {"prediction": predictions}


def json_serialize_predictions(example):
    # We serialize the predictions to JSON
    example["prediction"] = json.dumps(example["prediction"])
    return example


def infer_loop(workdir, input_filepath: str, batch_size: int, output_filepath: Optional[str] = None):
    if not output_filepath:
        output_filepath = os.path.join(workdir, "output.csv")

    # This is assuming the file is in csv format
    dataset = load_dataset("csv", data_files=[input_filepath])["train"]
    dataset = dataset.map(infer, batched=True, batch_size=batch_size)
    # We json serialize the predictions because they are python lists
    dataset = dataset.map(json_serialize_predictions)
    dataset.to_csv(output_filepath)
    return output_filepath


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_bucket_name", type=str, required=True)
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_bucket_name", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, required=False, default=4)
    parser.add_argument("--local", action="store_true", default=False)
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        input_workdir = os.path.join(tmpdir, "input")
        os.makedirs(input_workdir, exist_ok=True)

        output_workdir = os.path.join(tmpdir, "output")
        os.makedirs(output_workdir, exist_ok=True)

        # Download the input files
        if not args.local:
            input_filepath = download_input_files(
                workdir=input_workdir,
                input_bucket_name=args.input_bucket_name,
                input_path=args.input_path,
            )
        else:
            input_filepath = args.input_path

        # Perform Inference
        output_filepath = infer_loop(
            workdir=output_workdir,
            input_filepath=input_filepath,
            batch_size=args.batch_size,
            output_filepath=args.output_path if args.local else None,
        )

        # Upload the results to S3
        if not args.local:
            upload_output_files(
                output_filepath=output_filepath,
                output_bucket_name=args.output_bucket_name,
                output_path=args.output_path,
            )


if __name__ == "__main__":
    main()
