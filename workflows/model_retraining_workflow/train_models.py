import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from truefoundry.ml import get_client, ModelFramework
import joblib
from sklearn.metrics import f1_score

client = get_client()


def train_respective_model(
    model_algorithm: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    ml_repo: str,
) -> str:
    if model_algorithm == "random_forest":
        return train_random_forest(X_train, y_train, X_test, y_test, ml_repo)
    elif model_algorithm == "svm":
        return train_svm(X_train, y_train, X_test, y_test, ml_repo)
    elif model_algorithm == "knn":
        return train_knn(X_train, y_train, X_test, y_test, ml_repo)
    else:
        raise ValueError(f"Invalid model algorithm: {model_algorithm}")


# Train Random Forest
def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    ml_repo: str,
) -> str:
    print("Training Random Forest model")
    run = client.create_run(ml_repo=ml_repo)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    scores = model.predict(X_test)
    f1 = f1_score(y_test, scores)
    run.log_metrics(
        {
            "algoritm": "random_forest",
            "accuracy": model.score(X_train, y_train),
            "f1": f1,
        }
    )
    joblib.dump(model, "model.pkl")
    run.log_model(
        name="random_forest_model",
        model_file_or_folder="model.pkl",
        framework=ModelFramework.SKLEARN,
    )
    return run.fqn


# Train SVM
def train_svm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    ml_repo: str,
) -> str:
    print("Training SVM model")
    run = client.create_run(ml_repo=ml_repo)

    model = SVC(kernel="linear")
    model.fit(X_train, y_train)
    scores = model.predict(X_test)
    f1 = f1_score(y_test, scores)
    run.log_metrics(
        {
            "algoritm": "random_forest",
            "accuracy": model.score(X_train, y_train),
            "f1": f1,
        }
    )
    joblib.dump(model, "model.pkl")
    run.log_model(
        name="svm_model",
        model_file_or_folder="model.pkl",
        framework=ModelFramework.SKLEARN,
    )
    return run.fqn


# Train KNN
def train_knn(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    ml_repo: str,
) -> str:
    print("Training KNN model")
    run = client.create_run(ml_repo=ml_repo)

    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X_train, y_train)
    scores = model.predict(X_test)
    f1 = f1_score(y_test, scores)
    run.log_metrics(
        {
            "algoritm": "random_forest",
            "accuracy": model.score(X_train, y_train),
            "f1": f1,
        }
    )
    joblib.dump(model, "model.pkl")
    run.log_model(
        name="knn_model",
        model_file_or_folder="model.pkl",
        framework=ModelFramework.SKLEARN,
    )
    return run.fqn
