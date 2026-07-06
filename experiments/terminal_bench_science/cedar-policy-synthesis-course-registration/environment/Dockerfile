FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    python3 \
    python3-pip \
    python3-pytest \
    cargo \
    cvc5 \
    && rm -rf /var/lib/apt/lists/*

RUN cargo install cedar-policy-cli --locked --version 4.10.0 --features analyze
