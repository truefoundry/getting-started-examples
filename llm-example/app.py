import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI, Query
from llm import llm

artifact_downloaded_path = os.environ["CLASSIFIER_MODEL_PATH"]
classifier = joblib.load(os.path.join(artifact_downloaded_path, "iris_classifier.joblib"))

app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH", "/"))

IRIS_CLASSES = {0: "Setosa", 1: "Versicolour", 2: "Virginica"}


@app.post("/prompt")
def predict(
    prompt: str = Query(
        default="The flower has a sepal length of 5.1cm, a sepal width of 3.5cm, a petal length of 1.4cm and a petal width of 0.2cm."
    ),
):
    response = llm(prompt=prompt)
    data = json.loads(response)
    prediction = int(classifier.predict(pd.DataFrame([data]))[0])
    return {"flower_name": IRIS_CLASSES[prediction], "features": data}
