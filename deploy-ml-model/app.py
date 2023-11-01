import os
import joblib
import pandas as pd
from fastapi import FastAPI

# Load the pre-trained machine learning model
model = joblib.load("iris_classifier.joblib")

# Create a FastAPI app instance with custom configuration
app = FastAPI(docs_url="/", root_path=os.getenv("TFY_SERVICE_ROOT_PATH", "/"))

# Define an API endpoint for making predictions
@app.post("/predict")
def predict(
    sepal_length: float, sepal_width: float, petal_length: float, petal_width: float
):
    # Create a dictionary with input data
    data = dict(
        sepal_length=sepal_length,
        sepal_width=sepal_width,
        petal_length=petal_length,
        petal_width=petal_width,
    )
    # Make a prediction using the loaded model
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    # Return the prediction as a JSON response
    return {"prediction": prediction}

