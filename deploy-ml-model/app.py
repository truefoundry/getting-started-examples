import os

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging

model = joblib.load("iris_classifier.joblib")
app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH"))


@app.post("/predict")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    data = dict(
        sepal_length=sepal_length,
        sepal_width=sepal_width,
        petal_length=petal_length,
        petal_width=petal_width,
    )
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    return {"prediction": prediction}

@app.middleware("http")
async def log_request(request: Request, call_next):
    body = await request.body()
    print(f"Request path: {request.url.path}")
    print(f"Request method: {request.method}")
    print(f"Request query params: {request.query_params}")
    print(f"Request body: {body.decode()}")
    response = await call_next(request)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
