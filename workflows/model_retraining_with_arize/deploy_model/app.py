import datetime
import os
import uuid
from typing import List

import joblib
import numpy as np
from arize.api import Client
from arize.utils.types import Environments, ModelTypes
from fastapi import FastAPI
from pydantic import BaseModel

# Load the saved model
model_path = os.path.join(os.environ.get("MODEL_DOWNLOAD_PATH", "."), "model.pkl")
# model_path = "model.pkl"
model = joblib.load(model_path)
logger = None

API_KEY = os.environ.get("ARIZE_API_KEY")  # If passing api_key via env vars
SPACE_ID = os.environ.get("ARIZE_SPACE_ID")  # If passing space_id via env vars

arize_client = Client(space_id=SPACE_ID, api_key=API_KEY)


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
        # logger.log(customer_dict)
        _ = arize_client.log(
            prediction_id=str(uuid.uuid4()),
            model_id="<model-id>",
            model_type=ModelTypes.BINARY_CLASSIFICATION,
            environment=Environments.PRODUCTION,
            model_version="v1",
            prediction_timestamp=int(datetime.datetime.now().timestamp()),
            prediction_label=results[i],
            features=customer_dict,
        )

    return {"predictions": results}
