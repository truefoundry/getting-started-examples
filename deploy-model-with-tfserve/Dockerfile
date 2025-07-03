# Use tensorflow/tensorflow:2.19.0-gpu for GPU support
FROM tensorflow/serving:2.19.0
COPY batching.config /batching.config
ENV MODEL_DIR=/models/mnist
ENTRYPOINT ["tensorflow_model_server"]
CMD ["--model_name", "mnist", "--model_base_path", "$MODEL_DIR", "--enable_batching", "--batching_parameters_file=/batching.config", "--rest_api_port=8000", "--rest_api_timeout_in_ms=10000", "--enable_model_warmup"]
