import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

model = joblib.load("iris_classifier.joblib")
app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH"))


class IrisRequest(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


@app.post("/predict")
def predict(request: IrisRequest):
    print(f"Received request: {request}")
    data = dict(
        sepal_length=request.sepal_length,
        sepal_width=request.sepal_width,
        petal_length=request.petal_length,
        petal_width=request.petal_width,
    )
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    print(f"Prediction: {prediction}")
    return {"prediction": prediction}
