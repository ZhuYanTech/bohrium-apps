# PLIP 玻尔 App — Dockerfile
# 基础镜像：python:3.12-slim（不直接用 pharmai/plip:latest，因为要把
# run_plip.py 一起打进去，且 pip 安装的 plip==3.0.1 已自带 openbabel wheel，
# 版本可钉死、可复现；pharmai/plip:latest 作为备选见下方注释）。
# 注意：必须用 3.12，不能用 3.11——requirements-plip.txt 里钉的 numpy==2.5.4
# 要求 Python >=3.12，在 3.11 上 pip 装不上。
# 构建：docker build -t plip-bohrium-app:1.0 .
# 运行：docker run --rm -v "$PWD:/work" plip-bohrium-app:1.0 \
#          --pdb-id 1VSN --out-dir /work/plip-output
FROM python:3.12-slim

LABEL org.opencontainers.image.title="PLIP 蛋白-配体相互作用分析（玻尔 App）"
LABEL org.opencontainers.image.description="PLIP 3.0.1, GPLv2. Upload PDB / PDB ID, output interaction table + Chinese report."
LABEL org.opencontainers.image.source="https://github.com/pharmai/plip"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖：PLIP 需要 OpenBabel（pip 的 openbabel wheel 已含二进制，
# 这里只补编译期缺失的库以防万一；如构建失败可去掉 libgomp1 之外的行）
# 玻尔要求镜像装 SSH 相关组件（openssh-server / supervisor / net-tools），
# 否则管理节点可能用不了；任务提交本身不受影响。
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        openssh-server \
        supervisor \
        net-tools \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 钉死版本：plip 3.0.1 / openbabel 3.2.1 / numpy 2.5.4 / lxml 6.1.3
COPY requirements-plip.txt ./
RUN pip install --no-cache-dir -r requirements-plip.txt

# DP-Launching 依赖（标准离线任务型 App 用；alpha 版，见 requirements-launching.txt）
COPY requirements-launching.txt ./
RUN pip install --no-cache-dir -r requirements-launching.txt

COPY run_plip.py launching.py ./

# 默认以非 root 运行（玻尔上跑任务时也更安全）
RUN useradd -m -u 10001 plipuser && chown -R plipuser:plipuser /app
USER plipuser

ENTRYPOINT ["python", "run_plip.py"]
# 注意：ENTRYPOINT 仍是 CLI；玻尔标准离线任务的 EntryPoint 在建版本时
# 另填镜像里的绝对路径 /app/launching.py（见 bohrium/bohrium-publish.md）。
CMD ["--help"]

# 备选方案（不推荐作默认）：直接用官方镜像
#   FROM pharmai/plip:latest
#   该镜像已含 PLIP + OpenBabel，但需另装 Python 依赖并确认入口命令，
#   且 latest 标签不可复现，故本仓库默认不用。
