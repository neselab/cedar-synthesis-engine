FROM rust:1-bookworm AS cedar-builder

ARG CEDAR_POLICY_CLI_VERSION=

RUN if [ -n "$CEDAR_POLICY_CLI_VERSION" ]; then \
        cargo install cedar-policy-cli --locked --version "$CEDAR_POLICY_CLI_VERSION" --features analyze; \
    else \
        cargo install cedar-policy-cli --locked --features analyze; \
    fi

FROM python:3.12-bookworm

ENV PYTHONUNBUFFERED=1 \
    CEDAR=/usr/local/bin/cedar \
    CVC5=/usr/bin/cvc5

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates cvc5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=cedar-builder /usr/local/cargo/bin/cedar /usr/local/bin/cedar

WORKDIR /app
COPY pyproject.toml README.md LICENSE MANIFEST.in ./
COPY autocedar ./autocedar

RUN pip install --no-cache-dir .

ENTRYPOINT ["autocedar"]
