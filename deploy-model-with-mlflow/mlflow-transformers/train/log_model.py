import mlflow
import transformers
import torch

pipeline = transformers.pipeline(
    task="text-generation",
    model="Qwen/Qwen2.5-0.5B-Instruct",
    device="cpu",
    torch_dtype=torch.float16,
)

with mlflow.start_run():
    mlflow.transformers.log_model(
        task="llm/v1/chat",
        transformers_model=pipeline,
        artifact_path="model",
        # Set save_pretrained to False to save storage space
        save_pretrained=False,
        registered_model_name="qwen2.5-0.5b-instruct",
    )
