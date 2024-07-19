from typing import Dict, Union

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier as Classification
from truefoundry.ml import ModelFramework, get_client


def track_experiment(ml_repo: str, model, params: Dict[str, str], metrics: Dict[str, Union[int, float]]):
    # initialize the TrueFoundry ML client.
    client = get_client()

    # create a run
    run = client.create_run(ml_repo=ml_repo, run_name="churn-train-job")
    # log the hyperparameters
    run.log_params(params)
    # log the metrics
    run.log_metrics(metrics)

    # dump the model and then save it.
    joblib.dump(model, "classifier.joblib")

    # log the model
    model_version = run.log_model(
        name="churn-model",
        # Path to the folder where the model is saved locally
        model_file_or_folder="classifier.joblib",
        # specify the framework used (in this case sklearn)
        framework=ModelFramework.SKLEARN,
        description="churn-prediction-model",
    )
    print(f"Model has been logged as {model_version.fqn}")
    # return the model's fqn
    return model_version.fqn


def train_model(n_neighbors: int, weights: str, ml_repo: str):
    df = pd.read_csv("https://raw.githubusercontent.com/nikp1172/datasets-sample/main/Churn_Modelling.csv")
    X = df.iloc[:, 3:-1].drop(["Geography", "Gender"], axis=1)
    y = df.iloc[:, -1]
    # Create train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the KNN Classifier
    classifier = Classification(
        n_neighbors=n_neighbors,
        weights=weights,
    )

    # Fit the classifier with the training data
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)

    # Get the metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred, average="weighted"),
        "precision": precision_score(y_test, y_pred, average="weighted"),
        "recall": recall_score(y_test, y_pred, average="weighted"),
    }

    # Log the experiment
    track_experiment(ml_repo=ml_repo, model=classifier, params=classifier.get_params(), metrics=metrics)


if __name__ == "__main__":
    import argparse

    # Setup the argument parser by instantiating `ArgumentParser` class
    parser = argparse.ArgumentParser()
    # Add the hyperparameters as arguments
    parser.add_argument(
        "--ml_repo",
        type=str,
        required=True,
        help="The name of the ML Repo to track metrics and models. You can create one from the ML Repos Tab on the UI",
    )
    parser.add_argument(
        "--n_neighbors",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--weights",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    # Train the model
    train_model(**vars(args))
