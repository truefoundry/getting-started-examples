FROM python:3.11-slim

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt .
RUN python -m venv .venv && \
    python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
