import os

import requests

SYSTEM_PROMPT = """
Given a natural language description of a flower's sepal and petal measurements as input, return a dictionary with the measurements. If a measurement is not mentioned, set its value to 0. The input sentence will contain descriptions of the sepal length, sepal width, petal length, and petal width.

For example, given the input 'The flower has a sepal length of 5.1 cm and a petal width of 0.3 cm.', the function should return: { 'sepal_length': 5.1, 'sepal_width': 0, 'petal_length': 0, 'petal_width': 0.3 }

Another example input could be 'This flower's sepal width is 3.5 cm and its petal length is 1.4 cm.', which should return: { 'sepal_length': 0, 'sepal_width': 3.5, 'petal_length': 1.4, 'petal_width': 0 }

INPUT:
"""

TFY_LLM_GATEWAY_HOST = os.getenv("TFY_LLM_GATEWAY_HOST")
TFY_API_KEY = os.getenv("TFY_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")


def llm(prompt):
    response = requests.post(
        TFY_LLM_GATEWAY_HOST,
        headers={
            "Authorization": f"Bearer {TFY_API_KEY}",
        },
        json={
            "prompt": SYSTEM_PROMPT + prompt,
            "model": MODEL_NAME,
            "max_tokens": 200,
        },
    )
    data = response.json()
    output = data["choices"][0]["text"]
    return output
