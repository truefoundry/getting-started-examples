FROM python:3.11-slim
WORKDIR /app
COPY ./requirements.txt /tmp/
RUN pip install -U pip setuptools wheel && pip install -r /tmp/requirements.txt
COPY . /app
ENTRYPOINT python app.py
