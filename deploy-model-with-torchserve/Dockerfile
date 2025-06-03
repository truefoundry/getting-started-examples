# Use pytorch/torchserve:0.12.0-gpu for GPU support
FROM pytorch/torchserve:0.12.0-cpu

WORKDIR /home/model-server

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Here we are copying the models to the image. But for large models it is recommended to cache the models in a volume.
# See: https://docs.truefoundry.com/docs/download-and-cache-models#download-models-and-artifacts
COPY model_store/ model_store/

COPY config.properties config.properties

ENTRYPOINT ["torchserve"]
CMD ["--foreground", "--start", "--ts-config", "/home/model-server/config.properties", "--disable-token-auth", "--enable-model-api", "--models", "all"]
