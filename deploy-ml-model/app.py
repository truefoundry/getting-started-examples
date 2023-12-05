import os
import joblib
import pandas as pd
from fastapi import FastAPI

download_path = os.getenv("MODEL_ID", ".")
model = None
for _, _ , files in os.walk(download_path):
    for file in files:
        if file.endswith(".joblib"):
            model = joblib.load(os.path.join(download_path, file))
            break

app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH", "/"))


@app.post("/predict")
def predict(
    sepal_length: float, sepal_width: float, petal_length: float, petal_width: float
):
    data = dict(
        sepal_length=sepal_length,
        sepal_width=sepal_width,
        petal_length=petal_length,
        petal_width=petal_width,
    )
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    return {"prediction": prediction}

