FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="Protein Aliphatic Index" \
      org.opencontainers.image.source="https://github.com/ZhuYanTech/bohrium-apps"

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server supervisor net-tools ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-launching.txt ./
RUN python -m pip install -r requirements-launching.txt
COPY run_aliphatic_index.py launching.py ./
COPY examples/ ./examples/
RUN chmod +x /app/launching.py && bash examples/test_run.sh && python launching.py --help
