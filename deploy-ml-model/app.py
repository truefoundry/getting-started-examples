import os
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel


model = joblib.load("iris_classifier.joblib")

app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH", "/"))

class FlowerItem(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.post("/predict")
def predict(
    flower_item: FlowerItem,
):
    data = dict(
        sepal_length=flower_item.sepal_length,
        sepal_width=flower_item.sepal_width,
        petal_length=flower_item.petal_length,
        petal_width=flower_item.petal_width,
    )
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    return {"prediction": prediction}

