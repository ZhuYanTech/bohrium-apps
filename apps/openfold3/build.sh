#!/usr/bin/env bash
# build.sh — OpenFold3 镜像的构建脚本（由 Dockerfile 分步调用，每步一个镜像层）。
#
# 用法：
#   bash build.sh all          # 全部步骤（本地手动构建用）
#   bash build.sh torch-a      # PyTorch 依赖 A：cuDNN
#   bash build.sh torch-b      # PyTorch 依赖 B：BLAS 与求解器
#   bash build.sh torch-c      # PyTorch 依赖 C：稀疏、集合通信与 FFT
#   bash build.sh torch-d      # PyTorch 依赖 D：其余 CUDA 运行时库与绑定
#   bash build.sh torch-wheel  # PyTorch 2.10 本体（不含依赖）
#   bash build.sh torch-extra  # PyTorch 其余依赖：triton 与纯 Python 包
#   bash build.sh torch        # 以上 6 步合起来
#   bash build.sh openfold3    # OpenFold3 0.5.0 与 Launching SDK
#   bash build.sh openbabel    # OpenBabel
#   bash build.sh checkpoint   # 下载 OpenBind-0 检查点（约 2.29 GB）
#   bash build.sh init         # 初始化 OpenFold3（CCD）+ 校验
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

# PyTorch 2.10.0+cu129 的依赖（精确版本取自 torch wheel 的 METADATA，
# 与 torch 2.10.0 配套；分 6 步装，每步一个镜像层，单层控制在约 1.2 GB 以内，
# 避免超过 Bohrium 仓库的单层上限）。
TORCH_INDEX=https://download.pytorch.org/whl/cu129
# A：cuDNN（最大的一块，单独一层）
NVIDIA_A="nvidia-cudnn-cu12==9.10.2.21"
# B：BLAS 与求解器
NVIDIA_B="nvidia-cublas-cu12==12.9.1.4 nvidia-cusolver-cu12==11.7.5.82"
# C：稀疏、集合通信与 FFT
NVIDIA_C="nvidia-cusparse-cu12==12.5.10.65 nvidia-nccl-cu12==2.27.5 nvidia-cufft-cu12==11.4.1.4"
# D：其余 CUDA 运行时库与绑定
NVIDIA_D="nvidia-curand-cu12==10.3.10.19 nvidia-cusparselt-cu12==0.7.1 nvidia-nvshmem-cu12==3.4.5 nvidia-cuda-nvrtc-cu12==12.9.86 nvidia-cuda-runtime-cu12==12.9.79 nvidia-cuda-cupti-cu12==12.9.79 nvidia-nvtx-cu12==12.9.79 nvidia-nvjitlink-cu12==12.9.86 nvidia-cufile-cu12==1.14.1.1 cuda-bindings==12.9.4"

step_torch_a() {
  echo "== 安装 PyTorch 依赖 A：cuDNN =="
  python3 -m pip install --no-cache-dir --index-url "$TORCH_INDEX" $NVIDIA_A
}

step_torch_b() {
  echo "== 安装 PyTorch 依赖 B：BLAS 与求解器 =="
  python3 -m pip install --no-cache-dir --index-url "$TORCH_INDEX" $NVIDIA_B
}

step_torch_c() {
  echo "== 安装 PyTorch 依赖 C：稀疏、集合通信与 FFT =="
  python3 -m pip install --no-cache-dir --index-url "$TORCH_INDEX" $NVIDIA_C
}

step_torch_d() {
  echo "== 安装 PyTorch 依赖 D：其余 CUDA 运行时库与绑定 =="
  python3 -m pip install --no-cache-dir --index-url "$TORCH_INDEX" $NVIDIA_D
}

step_torch_wheel() {
  echo "== 安装 PyTorch 2.10 本体（不含依赖）=="
  python3 -m pip install --no-cache-dir --no-deps --index-url "$TORCH_INDEX" torch==2.10.0
}

step_torch_extra() {
  echo "== 安装 PyTorch 其余依赖：triton 与纯 Python 包 =="
  python3 -m pip install --no-cache-dir --index-url "$TORCH_INDEX" triton==3.6.0 filelock "typing-extensions>=4.10.0" "sympy>=1.13.3" "networkx>=2.5.1" jinja2 "fsspec>=0.8.5"
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
  torch-a) step_torch_a ;;
  torch-b) step_torch_b ;;
  torch-c) step_torch_c ;;
  torch-d) step_torch_d ;;
  torch-wheel) step_torch_wheel ;;
  torch-extra) step_torch_extra ;;
  torch) step_torch_a; step_torch_b; step_torch_c; step_torch_d; step_torch_wheel; step_torch_extra ;;
  openfold3) step_openfold3 ;;
  openbabel) step_openbabel ;;
  checkpoint) step_checkpoint ;;
  init) step_init ;;
  all) step_torch_a; step_torch_b; step_torch_c; step_torch_d; step_torch_wheel; step_torch_extra; step_openfold3; step_openbabel; step_checkpoint; step_init ;;
  *) echo "未知步骤：$1（可用：torch-a / torch-b / torch-c / torch-d / torch-wheel / torch-extra / torch / openfold3 / openbabel / checkpoint / init / all）" >&2; exit 2 ;;
esac
