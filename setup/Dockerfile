ARG DEVICE_TYPE=gpu
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS gpu-base
FROM ubuntu:22.04 AS cpu-base
FROM ${DEVICE_TYPE}-base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-dev \
    ffmpeg \
    build-essential \
    make \ 
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --set python3 /usr/bin/python3.11

ENV DEVICE_TYPE=${DEVICE_TYPE} \
    GOOGLE_APPLICATION_CREDENTIALS=/gcp/credentials.json

COPY . .

RUN python3 setup/build.py

RUN chmod +x /app/setup/entrypoint.sh

ENTRYPOINT ["/app/setup/entrypoint.sh"]