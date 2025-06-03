import datetime
import random
from functools import partial
from typing import List, Tuple

import numpy as np
import pandas as pd
import whylogs as why
from deploy_model.deploy import deploy_service
from sklearn.model_selection import train_test_split
from train_models import train_respective_model
from truefoundry.deploy import Resources
from truefoundry.ml import get_client
from truefoundry.workflow import (
    ExecutionConfig,
    PythonTaskConfig,
    TaskPythonBuild,
    map_task,
    task,
    workflow,
)
from whylogs.api.writer.whylabs import WhyLabsWriter

task_config = PythonTaskConfig(
    image=TaskPythonBuild(
        python_version="3.10",
        pip_packages=["truefoundry[workflow]>=0.9.2,<0.10.0"],
        requirements_path="requirements.txt",
    ),
    resources=Resources(
        cpu_request=1,
        cpu_limit=1,
        memory_request=1000,
        memory_limit=1500,
        ephemeral_storage_request=1000,
        ephemeral_storage_limit=1500,
    ),
    env={
        "TFY_API_KEY": "<Your-pat-token>",
        "TFY_HOST": "<host>",
        "WHYLABS_DEFAULT_ORG_ID": "<org-id>",
        "WHYLABS_DEFAULT_DATASET_ID": "<dataset-id>",
        "WHYLABS_API_KEY": "<api-key>",
    },
)


# This is a dummy function to simulate drift detection, In actual implementation one would fetch anomaly from whylabs or this workflow will be triggered when whylabs sends a webhook event(https://docs.whylabs.ai/docs/)
@task(task_config=task_config)
def check_drift() -> bool:
    drift_value = random.randint(1, 10)
    if drift_value > 5:
        print("Drift is detected in the data")
        return True
    print("No drift detected in the data")
    return False


@task(task_config=task_config)
def load_and_preprocess_data(
    is_drift_present: bool,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not is_drift_present:
        print("No drift detected in the data, skipping data preprocessing")
        return (np.array([]), np.array([]), np.array([]), np.array([]))

    # In case of drift, the latest data will be fetched from external source, we are just using data.csv for demo purpose.
    df = pd.read_csv("data.csv")

    df = df.drop(["RowNumber", "CustomerId", "Surname"], axis=1)

    df["Geography"] = df["Geography"].map({"France": 0, "Germany": 1, "Spain": 2})
    df["Gender"] = df["Gender"].map({"Male": 1, "Female": 0})

    X = df.drop("Exited", axis=1)
    y = df["Exited"]
    new_df = df.rename(
        columns={"Exited": "Output"},
    )
    current_time = datetime.datetime.now().astimezone()
    profile = why.log(
        new_df,
        dataset_timestamp=current_time,
        name=f"train_data-{current_time.isoformat()}",
    )

    writer = WhyLabsWriter()
    writer.option(reference_profile_name=f"train_data-{current_time.isoformat()}")
    writer.write(profile)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return (X_train.values, X_test.values, y_train.values, y_test.values)


@task(task_config=task_config)
def train_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    ml_repo: str,
    model_algorithm: str,
    is_drift_present: bool,
) -> str:
    if not is_drift_present:
        print("No drift detected in the data, skipping model training")
        return "No drift detected in the data"
    return train_respective_model(model_algorithm, X_train, y_train, X_test, y_test, ml_repo)


@task(task_config=task_config)
def evaluate_model(run_fqns: List[str], is_drift_present: bool) -> str:
    if not is_drift_present:
        print("No drift detected in the data, skipping model evaluation")
        return "No drift detected in the data"

    client = get_client()
    best_model_run_fqn = None
    best_accuracy = 0
    for run_fqn in run_fqns:
        run = client.get_run_by_fqn(run_fqn)
        metrics = run.get_metrics()
        f1_score = metrics.get("f1", 0)[0].value
        if f1_score > best_accuracy:
            best_accuracy = f1_score
            best_model_run_fqn = run_fqn
    return best_model_run_fqn


@task(task_config=task_config)
def deploy_model(run_fqn: str, workspace_fqn: str, is_drift_present: bool) -> str:
    if not is_drift_present:
        print("No drift detected in the data, skipping model deployment")
        return "No drift detected in the data"

    client = get_client()
    run = client.get_run_by_fqn(run_fqn)
    models = run.list_model_versions()
    model = models.__next__()
    print(f"Deploying model {model.fqn}")
    url = deploy_service(model_version_fqn=model.fqn, workspace_fqn=workspace_fqn)
    return f"Model deployed at {url}"


@workflow(execution_configs=[ExecutionConfig(schedule="0 * * * *")])
def check_drift_and_train_model(ml_repo: str, workspace_fqn: str) -> str:
    is_drift_present = check_drift()
    X_train, X_test, y_train, y_test = load_and_preprocess_data(is_drift_present)
    partial_function = partial(
        train_models,
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        ml_repo=ml_repo,
        is_drift_present=is_drift_present,
    )
    run_fqns = map_task(partial_function)(model_algorithm=["random_forest", "svm", "knn"])
    best_model_run_fqn = evaluate_model(run_fqns, is_drift_present)
    url = deploy_model(
        run_fqn=best_model_run_fqn,
        workspace_fqn=workspace_fqn,
        is_drift_present=is_drift_present,
    )
    return url


if __name__ == "__main__":
    check_drift_and_train_model(
        ml_repo="<ml-repo>",
        workspace_fqn="<workspace-fqn>",
    )
