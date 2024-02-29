import os

import requests

SYSTEM_PROMPT = """
Given a natural language description of a flower's sepal and petal measurements as input, return a JSON object with the measurements. If a measurement is not mentioned, set its value to 0. The input sentence will contain descriptions of the sepal length, sepal width, petal length, and petal width.

For example:

Example 1:
Input: "The flower has a sepal length of 5.1cm, a sepal width of 3.5cm, a petal length of 1.4cm and a petal width of 0.2cm."

{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}


Example 2:
Input: "The sepal length measures 4.9cm and the sepal width is 3.0cm."

{"sepal_length": 4.9, "sepal_width": 3.0, "petal_length": 0, "petal_width": 0}

Input: 
"""

TFY_LLM_GATEWAY_HOST = os.environ[
    "TFY_LLM_GATEWAY_HOST"
]  # Ex: https://*.truefoundry.tech/v1/chat/completions

TFY_API_KEY = os.environ["TFY_API_KEY"]
LLM_MODEL = os.environ["LLM_MODEL"]


def llm(prompt):
    response = requests.post(
        TFY_LLM_GATEWAY_HOST,
        headers={
            "Authorization": f"Bearer {TFY_API_KEY}",
        },
        json={
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "model": LLM_MODEL,
            "max_tokens": 200,
        },
    )
    response.raise_for_status()
    data = response.json()
    output = data["choices"][0]["message"]["content"]
    return output
