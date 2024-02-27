import os

import requests

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT") or ""


def llm(prompt):
    response = requests.post(
        os.getenv("TRUEFOUNDRY_API_ENDPOINT"),
        headers={
            "Authorization": f"Bearer {os.getenv('TRUEFOUNDRY_API_KEY')}",
        },
        json={
            "prompt": SYSTEM_PROMPT + prompt,
            "model": os.getenv("TRUEFOUNDRY_MODEL"),
            "temperature": 0.5,
            "max_tokens": 200,
            "top_p": 1.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
    )
    data = response.json()
    output = data["choices"][0]["text"]
    return output
