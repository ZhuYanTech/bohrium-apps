FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    openssh-server supervisor net-tools ca-certificates \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*_key*

WORKDIR /app
COPY requirements-launching.txt ./
RUN python -m pip install -r requirements-launching.txt
RUN python -m pip install biopython==1.85 numpy==1.26.4
RUN python -m pip install matplotlib==3.10.8
ENV PYTHONPATH=/usr/lib/python3/dist-packages MPLBACKEND=Agg
COPY *.py ./
COPY examples/ ./examples/

LABEL org.opencontainers.image.title="hydropathy-plot" \
      org.opencontainers.image.source="https://github.com/ZhuYanTech/bohrium-apps"
RUN bash examples/test_run.sh
