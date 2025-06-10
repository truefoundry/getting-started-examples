from mlflow.pyfunc.utils import pyfunc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pydantic
import mlflow


class SentimentRequest(pydantic.BaseModel):
    text: str


analyser = SentimentIntensityAnalyzer()


@pyfunc
def predict(model_input: list[SentimentRequest]) -> list[dict[str, float]]:
    return [analyser.polarity_scores(request.text) for request in model_input]


def _main():
    input_example = [SentimentRequest(text="I love this product!")]
    print(predict(input_example))
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=predict,
        registered_model_name="sentiment-model",
        input_example=[SentimentRequest(text="I love this product!")],
    )


if __name__ == "__main__":
    _main()
