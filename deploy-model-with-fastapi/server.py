import os
from contextlib import asynccontextmanager
from typing import Dict

import joblib
import pandas as pd
from fastapi import FastAPI

model = None
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.getenv("MODEL_DIR", THIS_DIR)
MODEL_PATH = os.path.join(MODEL_DIR, "iris_classifier.joblib")


def load_model():
    _model = joblib.load(MODEL_PATH)
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = load_model()
    yield


app = FastAPI(lifespan=lifespan, root_path=os.getenv("TFY_SERVICE_ROOT_PATH", ""))


@app.get("/health")
async def health() -> Dict[str, bool]:
    return {"healthy": True}


@app.post("/predict")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    global model
    class_names = ["setosa", "versicolor", "virginica"]
    data = dict(
        sepal_length=sepal_length,
        sepal_width=sepal_width,
        petal_length=petal_length,
        petal_width=petal_width,
    )
    prediction = model.predict_proba(pd.DataFrame([data]))[0]
    predictions = []
    for label, confidence in zip(class_names, prediction):
        predictions.append({"label": label, "score": confidence})
    return {"predictions": predictions}
