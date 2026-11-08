#!/usr/bin/env bash
# PLIP 镜像构建 + 推送到玻尔（Docker 机器上跑）
# 用法：在有 Docker + Node.js 的机器上，
#   先克隆仓库、进 apps/plip/，再跑：
#     bash build-and-push.sh
# 前置（只做一次，在这台机器的终端做）：
#   npm install -g @dptech-corp/bohr-cli@latest
#   bohr auth login          # 浏览器 SSO，用你的玻尔账号登录
#   bohr auth status --verify
# 发布前设置 PROJECT_ID 环境变量为你的玻尔项目 ID（数字），例如：
#   PROJECT_ID=1234567 bash build-and-push.sh
# 镜像：zhuyan/plip-bohrium-app:1.0（plip==3.0.1，CPU 即可）
set -euo pipefail
cd "$(dirname "$0")"

PROJECT_ID="${PROJECT_ID:?请设置 PROJECT_ID 环境变量（你的玻尔项目 ID，数字）}"
IMAGE_NAME="${IMAGE_NAME:-zhuyan/plip-bohrium-app:1.0}"

echo "== 1/3 docker build =="
docker build -t "$IMAGE_NAME" .

echo "== 2/3 本地冒烟：1VSN 应出 13 条相互作用 =="
docker run --rm "$IMAGE_NAME" --pdb-id 1VSN --out-dir /tmp/plip-smoke \
  || { echo "冒烟失败：容器没跑起来，先看上面日志"; exit 1; }
# 注意：容器内 /tmp/plip-smoke 随容器删除；只看退出码和日志里的计数。
# 如需留档，在宿主机挂载目录再跑一次：
#   docker run --rm -v "$PWD/smoke-output:/work" "$IMAGE_NAME" \
#     --pdb-id 1VSN --out-dir /work

echo "== 3/3 bohr 登记镜像并取 push 命令 =="
bohr image build --mode local \
  --dockerfile ./Dockerfile --context . \
  --name "$IMAGE_NAME" \
  --project-id "$PROJECT_ID" -o json | tee bohr-image-build.json
echo
echo "上面 JSON 里的 pushCommand 请原样执行一次（同一台机器、同一 Docker 环境），"
echo "不要自己拼 registry 地址。成功后核对返回的 imageUrl、digest、status=1，"
echo "把 imageUrl 记下来，继续建 App、上架。"
