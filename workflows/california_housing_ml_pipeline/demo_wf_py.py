from typing import Tuple, List, Dict, Union
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from truefoundry.workflow import (
    PythonTaskConfig,
    TaskPythonBuild,
    task,
    workflow,
    conditional,
    FlyteDirectory
)
from sklearn.base import BaseEstimator
from truefoundry.deploy import Resources
import joblib

task_config = PythonTaskConfig(
    image=TaskPythonBuild(
        python_version="3.9",
        pip_packages=["truefoundry[workflow,ml]==0.3.3", "scikit-learn==1.3.2", "pandas", "joblib"],
    ),
    resources=Resources(cpu_request=0.45),
    service_account="tfy-workflows-sa",
)


@task(task_config=task_config)
def load_and_split_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load the California Housing dataset and split it into train and test sets."""
    print("Starting to load and split data...")
    california = fetch_california_housing()
    X, y = california.data, california.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Data loaded and split. Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    return X_train, X_test, y_train, y_test

@task(task_config=task_config)
def preprocess_data(X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Standardize the features."""
    print("Starting data preprocessing...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("Data preprocessing completed.")
    return X_train_scaled, X_test_scaled, scaler

@task(task_config=task_config)
def select_features(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, k: int = 6) -> np.ndarray:
    """Select the top k features using f_regression."""
    print(f"Selecting top {k} features...")
    selector = SelectKBest(f_regression, k=k)
    X_train_selected = selector.fit_transform(X_train, y_train)
    print(f"Feature selection completed. Selected features shape: {X_train_selected.shape}")
    return X_train_selected

@task(task_config=task_config)
def train_complex_model(X_train: np.ndarray, y_train: np.ndarray) -> FlyteDirectory:
    """Train a Random Forest model with hyperparameter tuning."""
    print("Training complex model (Random Forest)...")
    param_dist = {
        'n_estimators': [100, 200, 300],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    rf = RandomForestRegressor(random_state=42)
    model_path = "./classifier.joblib"
    joblib.dump(rf, model_path)
    print("Complex model training completed and model saved.")
    return FlyteDirectory(path=".")

@task(task_config=task_config)
def train_simple_model(X_train: np.ndarray, y_train: np.ndarray) -> FlyteDirectory:
    """Train a simple Lasso model."""
    print("Training simple model (Lasso)...")
    model = Lasso(alpha=0.1, random_state=42)
    model.fit(X_train, y_train)
    model_path = "./classifier.joblib"
    joblib.dump(model, model_path)
    print("Simple model training completed and model saved.")
    return FlyteDirectory(path=".")

@workflow
def adaptive_california_housing_ml_pipeline(train_simple_lasso_model: bool = False) -> str:
    """Workflow for adaptive California Housing price prediction."""
    print("Starting adaptive California Housing ML pipeline...")
    X_train, X_test, y_train, y_test = load_and_split_data()
    
    X_train_scaled, X_test_scaled, _ = preprocess_data(X_train=X_train, X_test=X_test)
    X_train_selected = select_features(X_train=X_train_scaled, X_test=X_test_scaled, y_train=y_train, k=6)
    # Conditional branching based on dataset size
    model_path = (
        conditional("model_selection")
        .if_(train_simple_lasso_model == False)
        .then(train_complex_model(X_train=X_train_selected, y_train=y_train))
        .else_()
        .then(train_simple_model(X_train=X_train_selected, y_train=y_train))
    )
    X_train_selected >> model_path
    print("Adaptive California Housing ML pipeline completed.")
    return ""

if __name__ == "__main__":
    adaptive_california_housing_ml_pipeline(train_simple_lasso_model=False)
