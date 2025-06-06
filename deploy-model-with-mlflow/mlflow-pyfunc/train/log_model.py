import mlflow
from model import predict, SentimentRequest

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=predict,
    registered_model_name="sentiment-model",
    input_example=[SentimentRequest(text="I love this product!")],
)
