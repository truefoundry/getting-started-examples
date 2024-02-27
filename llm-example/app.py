import ast
import os

import joblib
import pandas as pd
from fastapi import FastAPI
from llm import llm

model = joblib.load("iris_classifier.joblib")

app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH", "/"))

IRIS_CLASSES = {0: "Setosa", 1: "Versicolour", 2: "Virginica"}


@app.post("/prompt")
def predict(prompt: str):

    response = llm(prompt=prompt)
    data = ast.literal_eval(response)
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    return {"flower_name": IRIS_CLASSES[prediction]}
