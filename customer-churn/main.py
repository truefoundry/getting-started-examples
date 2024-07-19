from truefoundry.ml import ModelFramework
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier as Classification
from truefoundry.ml import get_client
from joblib import dump


def experiment_track(model, params, metrics):
    # initialize the mlfoundry client.
    mlf_api = get_client()

    # create a ml repo
    mlf_api.create_ml_repo("churn-pred")
    # create a run
    mlf_run = mlf_api.create_run(ml_repo="churn-pred", run_name="churn-train-job")
    # log the hyperparameters
    mlf_run.log_params(params)
    # log the metrics
    mlf_run.log_metrics(metrics)

    # dump the model and then save it.
    path = dump(model, "classifier.joblib")

    # log the model
    model_version = mlf_run.log_model(
        name="churn-model",
        # Path to the folder where the model is saved locally
        model_file_or_folder=path[0],
        # specify the framework used (in this case sklearn)
        framework=ModelFramework.SKLEARN,
        description="churn-prediction-model",
    )
    # return the model's fqn
    return model_version.fqn


def train_model(hyperparams):
    df = pd.read_csv("https://raw.githubusercontent.com/nikp1172/datasets-sample/main/Churn_Modelling.csv")
    X = df.iloc[:, 3:-1].drop(["Geography", "Gender"], axis=1)
    y = df.iloc[:, -1]
    # Create train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the KNN Classifier
    classifier = Classification(
        n_neighbors=hyperparams["n_neighbors"],
        weights=hyperparams["weights"],
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
    experiment_track(classifier, classifier.get_params(), metrics)


if __name__ == "__main__":
    import argparse

    # Setup the argument parser by instantiating `ArgumentParser` class
    parser = argparse.ArgumentParser()
    # Add the hyperparameters as arguments
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
    hyperparams = vars(args)

    # Train the model
    train_model(hyperparams)
