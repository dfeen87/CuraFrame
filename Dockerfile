FROM python:3.11.14-slim-bookworm

RUN apt-get update \
    && apt-get install --no-install-recommends --yes build-essential make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/curaframe
COPY . .
RUN pip install --no-cache-dir -r requirements.txt pytest

RUN groupadd --gid 1000 developer \
    && useradd --uid 1000 --gid developer --create-home developer \
    && mkdir -p /repro \
    && chown developer:developer /repro

USER developer
WORKDIR /repro
VOLUME ["/repro"]

ENTRYPOINT ["make"]
