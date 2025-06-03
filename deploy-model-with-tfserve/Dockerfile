# Use tensorflow/tensorflow:2.19.0-gpu for GPU support
FROM tensorflow/serving:2.19.0

# Here we are copying the models to the image. But for large models it is recommended to cache the models in a volume.
# See: https://docs.truefoundry.com/docs/download-and-cache-models#download-models-and-artifacts
COPY models/ /models

ENTRYPOINT ["tensorflow_model_server"]
CMD ["--model_config_file=/models/models.config", "--enable_batching", "--batching_parameters_file=/models/batching.config", "--rest_api_port=8000", "--rest_api_timeout_in_ms=10000", "--enable_model_warmup"]
