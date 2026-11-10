#!/usr/bin/env bash
# build.sh — OpenFold3 镜像的构建脚本（由 Dockerfile 分步调用，每步一个镜像层）。
#
# 用法：
#   bash build.sh all          # 全部步骤（本地手动构建用）
#   bash build.sh torch        # 步骤 1：PyTorch 2.10（CUDA 12.9）
#   bash build.sh openfold3    # 步骤 2：OpenFold3 0.5.0 与 Launching SDK
#   bash build.sh openbabel    # 步骤 3：OpenBabel
#   bash build.sh checkpoint   # 步骤 4：下载 OpenBind-0 检查点（约 2.29 GB）
#   bash build.sh init         # 步骤 5：初始化 OpenFold3（CCD）+ 校验
#
# 分步原因：每步生成一个独立镜像层，避免单层过大被镜像仓库拒绝
# （此前单步约 14 GB，Bohrium 仓库返回 413 Request Entity Too Large）。
#
# 装什么：
#   - OpenFold3 0.5.0（Apache 2.0），含 run_openfold 命令
#   - PyTorch 2.10 + CUDA 12.9（GPU 运行用）
#   - OpenBabel（SDF → SMILES 转换）
#   - OpenBind-0 检查点（约 2.29 GB），烤进镜像
#   - Launching SDK（玻尔离线任务封装）
#   - SSH 组件（玻尔镜像必需：openssh-server、supervisor、net-tools、curl）
#
# 注意：
#   - setup_openfold --non-interactive 只在检查点不存在时才下载；
#     若本脚本已先下载好，它会跳过下载，只做 CCD 初始化。
#   - 集成测试不在构建期跑：需要 GPU 且 pytest 未装。
#   - 构建完成后，镜像内还需一个可用 OpenFold3 环境；
#     本机无 GPU 时只能跑 --dry-run 校验，不能做真实预测。
set -euo pipefail

APP_DIR=/app
CACHE_DIR=/opt/openfold3-cache
CKPT_NAME=of3-ob-2025-06-30-174k.pt
CKPT_URL=https://openfold3-data.s3.amazonaws.com/openfold3-parameters/of3-ob-2025-06-30-174k.pt
CKPT_SIZE=2287872989

step_torch() {
  echo "== 安装 PyTorch 2.10（CUDA 12.9）=="
  python3 -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu129 torch==2.10.0
}

step_openfold3() {
  echo "== 安装 OpenFold3 0.5.0 与 Launching SDK =="
  python3 -m pip install --no-cache-dir -r "$APP_DIR/requirements-openfold3.txt"
  python3 -m pip install --no-cache-dir -r "$APP_DIR/requirements-launching.txt"
}

step_openbabel() {
  echo "== 安装 OpenBabel（SDF 转换）=="
  apt-get update -qq && apt-get install -y --no-install-recommends openbabel
  rm -rf /var/lib/apt/lists/*
}

step_checkpoint() {
  echo "== 下载检查点 OpenBind-0（${CKPT_NAME}，约 2.29 GB）=="
  mkdir -p "$CACHE_DIR"
  curl -fSL --retry 3 -o "$CACHE_DIR/$CKPT_NAME" "$CKPT_URL"
  ACTUAL_SIZE=$(stat -c%s "$CACHE_DIR/$CKPT_NAME")
  if [ "$ACTUAL_SIZE" -ne "$CKPT_SIZE" ]; then
    echo "警告：检查点大小为 $ACTUAL_SIZE 字节，预期 $CKPT_SIZE 字节。"
    echo "请核对上游是否发布了新检查点；若确认无误，请更新 CKPT_SIZE。"
  fi
}

step_init() {
  echo "== 初始化 OpenFold3（CCD 组件，不跑集成测试）=="
  export OPENFOLD_CACHE="$CACHE_DIR"
  setup_openfold --non-interactive
  # 注意：setup_openfold 只在默认检查点不存在时才下载。
  # 本脚本已先下载好 OpenBind-0；若它仍下载了另一份检查点，
  # 下面的检查会列出所有 .pt 文件，首次构建时据此调整。

  echo "== 校验 =="
  python3 -c "import importlib.metadata; print('openfold3', importlib.metadata.version('openfold3'))"
  python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda)"
  test -s "$CACHE_DIR/$CKPT_NAME" && echo "检查点 OK: $CACHE_DIR/$CKPT_NAME"
  echo "镜像内所有检查点文件："
  find "$CACHE_DIR" -name "*.pt" -exec ls -lh {} \; 2>/dev/null || true
  which obabel && obabel -L formats | grep -q "smi" && echo "OpenBabel OK"
  python3 "$APP_DIR/run_openfold3.py" --help >/dev/null && echo "run_openfold3.py OK"
  echo "== 构建完成 =="
}

case "${1:-all}" in
  torch) step_torch ;;
  openfold3) step_openfold3 ;;
  openbabel) step_openbabel ;;
  checkpoint) step_checkpoint ;;
  init) step_init ;;
  all) step_torch; step_openfold3; step_openbabel; step_checkpoint; step_init ;;
  *) echo "未知步骤：$1（可用：torch / openfold3 / openbabel / checkpoint / init / all）" >&2; exit 2 ;;
esac
