# Use pytorch/torchserve:0.12.0-gpu for GPU support
FROM pytorch/torchserve:0.12.0-cpu

WORKDIR /home/model-server

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY config.properties config.properties

ENTRYPOINT ["torchserve"]
CMD ["--foreground", "--start", "--ts-config", "/home/model-server/config.properties", "--disable-token-auth", "--enable-model-api", "--models", "all"]
