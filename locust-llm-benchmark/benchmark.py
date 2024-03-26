import json
import os
import time

from locust import HttpUser, between, events, task

PROMPT = "Explain MLOps in 300 tokens or less."
TFY_HOST = os.getenv("TFY_HOST", "https://llm-gateway.truefoundry.com")
# or export self hosted url Ex: https://*.truefoundry.tech/

TFY_API_KEY = os.environ["TFY_API_KEY"]
LLM_MODEL = "truefoundry-public/Llama-2-Chat(7B)"


class StreamingUserBenchmark(HttpUser):
    wait_time = between(1, 3)
    host = TFY_HOST

    @task
    def llm_benchmark(self):
        data = json.dumps(
            {
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 1,
                "top_p": 1,
                "n": 1,
                "stream": True,
                "max_tokens": 100,
                "presence_penalty": 0,
                "frequency_penalty": 0,
            }
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {TFY_API_KEY}",
            # Set the tfy_log_request to "`true`" in X-TFY-METADATA header to log prompt and response for the request
            "X-TFY-METADATA": json.dumps(
                {"tfy_log_request": "true", "Custom-Metadata": "Custom-Value"}
            ),
        }

        start_time_streaming = time.time()
        first_token_done = False
        with self.client.post(
            "/api/llm/openai/chat/completions", headers=headers, data=data, stream=True
        ) as response:
            for line in response.iter_lines():
                if len(line) == 0:
                    continue
                string_object = line.decode("utf-8")
                if "data:" in string_object:
                    string_object = string_object.replace("data:", "")
                if "[DONE]" in string_object:
                    total_token_latency = (time.time() - start_time_streaming) * 1000
                    continue

                line_obj = json.loads(string_object)
                if "content" not in line_obj["choices"][0]["delta"]:
                    continue
                if (
                    not first_token_done
                    and len(line_obj["choices"][0]["delta"]) > 0
                    and line_obj["choices"][0]["delta"]["content"] != ""
                ):
                    first_token_latency = (time.time() - start_time_streaming) * 1000
                    first_token_done = True

        events.request.fire(
            request_type="METRIC",
            name=f"Total Token Latency",
            response_time=total_token_latency,
            response_length=len(line),
        )
        events.request.fire(
            request_type="METRIC",
            name=f"First Token Latency",
            response_time=first_token_latency,
            response_length=len(line),
        )
