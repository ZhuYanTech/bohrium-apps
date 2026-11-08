# Boltz-2 玻尔 App — Dockerfile
# 基础镜像：NVIDIA CUDA 12.4 运行时镜像（Ubuntu 22.04）+ Python 3.11。
# 必须用 GPU 镜像：Boltz-2 推理需要 CUDA，CPU 慢 50–100 倍，不可作为运行方式。
# Python 要求 3.10–<3.13，这里用 3.11（与社区容器一致）。
# 权重烤进镜像：约 6.2 GB（boltz2_conf.ckpt、boltz2_aff.ckpt、mols.tar），
# 构建时从 Hugging Face boltz-community/boltz-2 下载一次；运行时不再下载，
# 也不依赖节点能否访问 Hugging Face。
# 构建（需 Docker + 约 15 GB 磁盘，构建机不需要 GPU）：
#   docker build -t zhuyan/boltz2-bohrium-app:1.0 .
# 本地试运行（需 GPU）：
#   docker run --rm --gpus all -v "$PWD:/work" zhuyan/boltz2-bohrium-app:1.0 \
#     --sequence-file /work/examples/kras-g12c-sotorasib/sequence.txt \
#     --ligand-smiles "$(cat /work/examples/kras-g12c-sotorasib/ligand.smi)" \
#     --out-dir /work/boltz2-output
# 注意：本镜像尚未构建（无 GPU 的机器上无法验证推理部分），见 VERIFICATION.md。
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

LABEL org.opencontainers.image.title="Boltz-2 蛋白-配体共折叠与亲和力预测（玻尔 App）"
LABEL org.opencontainers.image.description="Boltz-2 v2.2.1, MIT. Protein-ligand co-folding + affinity prediction, Chinese report."
LABEL org.opencontainers.image.source="https://github.com/jwohlwend/boltz"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    BOLTZ_CACHE=/opt/boltz-cache

WORKDIR /app

# 系统依赖：Python 3.11 + pip；玻尔要求镜像装 SSH 相关组件
# （openssh-server / supervisor / net-tools），否则管理节点可能用不了；
# 任务提交本身不受影响。
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        openssh-server \
        supervisor \
        net-tools \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python3

# 钉死版本：boltz[cuda]==2.2.1（只用 MIT 的 2.2.1，不用 2.1），
# cuEquivariance==0.6.1（与社区容器一致的内核版本）。
COPY requirements-boltz2.txt ./
RUN pip install --no-cache-dir -r requirements-boltz2.txt

# 权重烤进镜像：从 Hugging Face 下载 boltz-community/boltz-2
# （boltz2_conf.ckpt、boltz2_aff.ckpt、mols.tar，合计约 6.2 GB）。
# huggingface_hub 随 boltz 一起装好；BOLTZ_CACHE 指向这里，运行时不再下载。
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download(repo_id='boltz-community/boltz-2', local_dir='/opt/boltz-cache')"

# DP-Launching 依赖（标准离线任务型 App 用；alpha 版，见 requirements-launching.txt）
COPY requirements-launching.txt ./
RUN pip install --no-cache-dir -r requirements-launching.txt

COPY run_boltz2.py launching.py ./

# 默认以非 root 运行（玻尔上跑任务时也更安全）
RUN useradd -m -u 10001 boltzuser && chown -R boltzuser:boltzuser /app /opt/boltz-cache
USER boltzuser

ENTRYPOINT ["python", "run_boltz2.py"]
# 注意：ENTRYPOINT 仍是 CLI；玻尔标准离线任务的 EntryPoint 在建版本时
# 另填镜像里的绝对路径 /app/launching.py（见 bohrium/bohrium-publish.md）。
CMD ["--help"]
