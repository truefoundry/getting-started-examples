import argparse
import joblib
import mlfoundry
from sklearn.base import accuracy_score
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

parser = argparse.ArgumentParser()
parser.add_argument("--ml_repo_name", type=str)
parser.add_argument("--n_estimators", type=int)
parser.add_argument("--max_depth", type=int)
parser.add_argument("--min_samples_leaf", type=int)
parser.add_argument("--criterion", type=str)

args = parser.parse_args()
client = mlfoundry.get_client()

X, y = load_iris(as_frame=True, return_X_y=True)
X = X.rename(columns={
        "sepal length (cm)": "sepal_length",
        "sepal width (cm)": "sepal_width",
        "petal length (cm)": "petal_length",
        "petal width (cm)": "petal_width",
})

# NOTE:- You can pass these configurations via command line
# arguments, config file, environment variables.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
# Initialize the model
clf = RandomForestClassifier(
    n_estimators=args.n_estimators,
    max_depth=args.max_depth,
    min_samples_leaf=args.min_samples_leaf,
    criterion=args.criterion
)
# Fit the model
clf.fit(X_train, y_train)

preds = clf.predict(X_test)
accuracy = accuracy_score(y_test, preds)

run = client.create_run(
    ml_repo=args.ml_repo_name,
    name="train", 
)
run.log_params(clf.get_params())
run.log_metrics({"accuracy": accuracy})
joblib.dump(clf, 'logistic_regression_model.joblib')

run.log_model(
    name="logistic-regression",
    model_file_or_folder="logistic_regression_model.joblib",
    framework="sklearn",
)