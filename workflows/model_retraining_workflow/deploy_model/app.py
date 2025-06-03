import logging
import os
from typing import List

import joblib
import numpy as np
import whylogs as why
from fastapi import FastAPI
from pydantic import BaseModel

logging.getLogger("whylabs").setLevel(logging.DEBUG)
# Load the saved model
model_path = os.path.join(os.environ.get("MODEL_DOWNLOAD_PATH", "."), "model.pkl")
model = joblib.load(model_path)
logger = None


# Define the FastAPI app
app = FastAPI()


# Define a request body model for a single customer
class CustomerData(BaseModel):
    CreditScore: float
    Geography: str
    Gender: str
    Age: int
    Tenure: int
    Balance: float
    NumOfProducts: int
    HasCrCard: int
    IsActiveMember: int
    EstimatedSalary: float


# Function to encode a single customer
def encode_input(data: CustomerData):
    gender = 1 if data.Gender.lower() == "male" else 0
    geography_map = {"France": 0, "Germany": 1, "Spain": 2}
    geography = geography_map.get(data.Geography, 0)

    # Return the processed input as a numpy array
    return np.array(
        [
            [
                data.CreditScore,
                gender,
                data.Age,
                data.Tenure,
                data.Balance,
                data.NumOfProducts,
                data.HasCrCard,
                data.IsActiveMember,
                data.EstimatedSalary,
                geography,
            ]
        ]
    )


# This funcition starts the whylogger logger and logs the prediction to whylabs every 5 minutes
@app.on_event("startup")
def start_logger():
    global logger
    logger = why.logger(mode="rolling", interval=300, when="S", base_name="fastapi_predictions")
    logger.append_writer("whylabs")


# Define a batch prediction endpoint that accepts a list of customers
@app.post("/predict_batch")
def predict_batch_churn(customers: List[CustomerData]):
    # Encode all customer inputs
    input_data = np.array([encode_input(customer)[0] for customer in customers])

    # Make predictions using the loaded model
    predictions = model.predict(input_data)

    results = [int(pred) for pred in predictions]

    # Log predictions and features to Arize
    for i, customer in enumerate(customers):
        customer_dict = customer.dict()
        customer_dict["output"] = results[i]
        logger.log(customer_dict)

    return {"predictions": results}


@app.on_event("shutdown")
def close_logger():
    logger.close()
