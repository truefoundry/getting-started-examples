import os
import joblib
import pandas as pd
import gradio as gr

model = joblib.load("iris_classifier.joblib")


def model_inference(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float) -> int:
    data = dict(
        sepal_length=sepal_length,
        sepal_width=sepal_width,
        petal_length=petal_length,
        petal_width=petal_width
    )
    prediction = int(model.predict(pd.DataFrame([data]))[0])
    return prediction


sepal_length_input = gr.Number(label="Enter the sepal length in cm")
sepal_width_input = gr.Number(label="Enter the sepal width in cm")
petal_length_input = gr.Number(label="Enter the petal length in cm")
petal_width_input = gr.Number(label="Enter the petal width in cm")

inputs = [sepal_length_input, sepal_width_input,
          petal_length_input, petal_width_input]

output = gr.Number()
print("Please don't merge")

gr.Interface(
    fn=model_inference,
    inputs=inputs,
    outputs=output,
).launch(server_name="0.0.0.0", server_port=8080)
