FROM public.ecr.aws/docker/library/ubuntu:24.04

ENV PYTHONUNBUFFERED TRUE

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    fakeroot \
    ca-certificates \
    dpkg-dev \
    g++ \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    openjdk-8-jdk-headless \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && cd /tmp \
    && curl -O https://bootstrap.pypa.io/get-pip.py \
    && python3.11 get-pip.py

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/local/bin/pip pip /usr/local/bin/pip3 1

RUN useradd -m model-server \
    && mkdir -p /home/model-server/tmp

WORKDIR /home/model-server

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Here we are copying the models to the image. But for large models it is recommended to cache the models in a volume.
# See: https://docs.truefoundry.com/docs/download-and-cache-models#download-models-and-artifacts
COPY model_store/ model_store/

COPY config.properties config.properties

ENTRYPOINT ["multi-model-server"]
CMD ["--foreground", "--start", "--mms-config", "/home/model-server/config.properties"]