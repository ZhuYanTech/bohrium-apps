FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    openssh-server supervisor net-tools ca-certificates \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*_key*

WORKDIR /app
COPY requirements-launching.txt ./
RUN python -m pip install -r requirements-launching.txt
RUN apt-get update && apt-get install -y --no-install-recommends openbabel && rm -rf /var/lib/apt/lists/*
COPY *.py ./
COPY examples/ ./examples/

LABEL org.opencontainers.image.title="open-babel" \
      org.opencontainers.image.source="https://github.com/ZhuYanTech/bohrium-apps"
RUN bash examples/test_run.sh
