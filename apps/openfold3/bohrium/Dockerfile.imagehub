# OpenFold3 结构预测（玻尔离线任务 App）
# 构建方式：把本文件全文粘贴到玻尔镜像中心（Image Hub）的 Dockerfile 输入框。
# 注意：本文件不含 COPY——构建时从公开仓库克隆封装脚本。
# 基础环境：Python 3.10、PyTorch 2.10、CUDA 12.9（OpenFold3 推荐环境）。
FROM nvidia/cuda:12.9.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    OPENFOLD_CACHE=/opt/openfold3-cache \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 1) 系统依赖：Python 3.10、构建工具、SSH 组件（玻尔镜像必需）、git/curl
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3.10-dev build-essential \
    openssh-server supervisor net-tools curl git \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir --upgrade pip

# 2) 从公开仓库取封装脚本（run_openfold3.py、launching.py、build.sh、requirements）
RUN mkdir -p /app && \
    git clone --depth 1 https://github.com/ZhuYanTech/bohrium-apps /tmp/bohrium-apps && \
    cp /tmp/bohrium-apps/apps/openfold3/run_openfold3.py \
       /tmp/bohrium-apps/apps/openfold3/launching.py \
       /tmp/bohrium-apps/apps/openfold3/build.sh \
       /tmp/bohrium-apps/apps/openfold3/requirements-openfold3.txt \
       /tmp/bohrium-apps/apps/openfold3/requirements-launching.txt /app/ && \
    chmod +x /app/build.sh /app/run_openfold3.py /app/launching.py && \
    rm -rf /tmp/bohrium-apps

# 3) 其余安装见 build.sh：PyTorch、OpenFold3、OpenBabel、检查点、Launching SDK
WORKDIR /app
RUN bash /app/build.sh

# 4) 镜像内默认用 --inference-ckpt-path 显式指定检查点（不依赖默认检查点名）
ENTRYPOINT ["python3", "run_openfold3.py"]
CMD ["--help"]
