from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import argparse
import mlfoundry
import os
import joblib
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--artifact_version_fqn", type=str)
parser.add_argument("--ml_repo_name", type=str)

args = parser.parse_args()

client = mlfoundry.get_client()

artifact_version = client.get_artifact_version_by_fqn(
    args.artifact_version_fqn
)
download_path = artifact_version.download(path=".", overwrite=True)

data_csv = None
for dirpath, dirnames, filenames in os.walk(download_path):
    for file in filenames:
        data_csv = pd.read_csv(os.path.join(download_path, file))
        break

if data_csv is None:
    raise Exception("No data found")

X = data_csv.iloc[:, :-1]
y = data_csv.iloc[:, -1]
X = X.rename(columns={
        "sepal.length": "sepal_length",
        "sepal.width": "sepal_width",
        "petal.length": "petal_length",
        "petal.width": "petal_width",
})

# NOTE:- You can pass these configurations via command line
# arguments, config file, environment variables.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
# Initialize the model
clf = LogisticRegression(solver="liblinear")
# Fit the model
clf.fit(X_train, y_train)

preds = clf.predict(X_test)
print(classification_report(y_true=y_test, y_pred=preds))
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
