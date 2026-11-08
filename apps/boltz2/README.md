# Boltz-2 共折叠与亲和力预测 — 玻尔（Bohrium）App

> 本 App 是 [`bohrium-apps`](https://github.com/ZhuYanTech/bohrium-apps) 单一仓库中的应用，位于 `apps/boltz2/`。
> 以下命令均在 `apps/boltz2/` 目录内执行。

输入蛋白氨基酸序列和配体 SMILES，一次推理同时给出预测复合物结构和
结合亲和力：结合概率（筛苗头）与预测 log10(IC50)（给相关化合物排序），
输出结构（PDB/CIF）、置信度与中文解读报告。

## 特点

- 结构 + 亲和力一次完成：与只做结构预测的工具互补，适合虚拟筛选、
  苗头到先导的排序。
- 亲和力默认开启，只针对排名第一的结构；结合概率用于区分结合物与诱饵，
  预测 log10(IC50) 用于相关化合物的排序。
- MSA 默认自动生成（公开 ColabFold 服务器），也可上传自备 `.a3m`。
- 权重烤进镜像（约 6.2 GB），运行时不再下载。

## 输入 / 输出

| | 内容 |
| --- | --- |
| 输入 | 蛋白氨基酸序列（单条链，粘贴或 FASTA，≤2900 个残基）；配体 SMILES（必填，二选一可填 CCD 编号）；可选 `.a3m` MSA 文件、口袋约束 |
| 输出 | `predicted.pdb`（排名第一的预测结构）、`confidence.json`（置信度）、`affinity.json`（亲和力）、`report_zh.md`（中文报告：置信度、亲和力换算、注意事项）、`input.yaml`（生成的 Boltz 输入）、`boltz_raw/`（Boltz 原生输出） |

## 默认值

| 参数 | 默认值 |
| --- | --- |
| 结构样本数 | 1 |
| 循环精修次数 | 3 |
| 结构采样步数 | 200 |
| 采样步长 | 1.5 |
| 输出格式 | PDB（CIF 也可选） |
| 亲和力 | 开启；亲和力样本 5、亲和力采样步 200 |
| MSA | 自动生成；最大 MSA 序列数 8192（Normal） |

## 本地运行（需要 GPU）

```bash
# 1. 装 Boltz-2（Python 3.10–<3.13，CUDA 12.x）
pip install 'boltz[cuda]==2.2.1'

# 2. 跑一个例子：KRAS G12C + 索托拉西布（共价抑制剂）
python3 run_boltz2.py \
  --sequence-file examples/kras-g12c-sotorasib/sequence.txt \
  --ligand-smiles "$(cat examples/kras-g12c-sotorasib/ligand.smi)" \
  --out-dir ./boltz2-output

# 3. 看结果
cat boltz2-output/report_zh.md
```

24 GB 显存起步（典型蛋白-配体复合物）；超过 1500 个残基建议用更大显存机型。
CPU 能跑但慢 50–100 倍，不可作为运行方式。

```bash
# 只验证输入并生成 YAML，不实际预测（无 GPU 时也能跑）
python3 run_boltz2.py \
  --sequence-file examples/kras-g12c-sotorasib/sequence.txt \
  --ligand-smiles "$(cat examples/kras-g12c-sotorasib/ligand.smi)" \
  --out-dir ./boltz2-output --dry-run

# 一键验证（无 GPU 可跑的检查：输入验证、YAML 生成、输出解析、Launching 入口）
bash examples/test_run.sh
```

## Docker 运行

```bash
docker build -t zhuyan/boltz2-bohrium-app:1.0 .
docker run --rm --gpus all -v "$PWD:/work" zhuyan/boltz2-bohrium-app:1.0 \
  --sequence-file /work/examples/kras-g12c-sotorasib/sequence.txt \
  --ligand-smiles "$(cat /work/examples/kras-g12c-sotorasib/ligand.smi)" \
  --out-dir /work/boltz2-output
```

镜像尚未构建（见 VERIFICATION.md）。

## MSA 三种模式

| 模式 | 做法 | 适用 |
| --- | --- | --- |
| 自动生成（默认） | `--use_msa_server`，调公开 ColabFold 服务器 | 大多数情况 |
| 上传 `.a3m` | `--msa-file xxx.a3m`，跳过自动生成 | 自备比对结果；第一条序列须与输入蛋白一致 |
| 单序列 | `--no-msa` | 只在自动生成失败时用；报告会注明“未使用 MSA，精度可能下降” |

三种分支由封装显式处理：Boltz 默认要求提供 MSA，不声明 opt-out 时
既不给 MSA 也不开自动生成会直接失败。

## 亲和力怎么读

- 结合概率 `affinity_probability_binary`（0–1）：用于区分结合物与诱饵，
  苗头发现阶段用；没有通用阈值，先拿靶点上已知活性化合物校准。
- 预测亲和力 `affinity_pred_value`（log10 IC50，单位 μM，越负结合越强）：
  用于苗头到先导、优化阶段给相关化合物排序。换算：−3 ≈ 1 nM、−2 ≈ 10 nM、
  −1 ≈ 100 nM、0 ≈ 1 μM、1 ≈ 10 μM、2 ≈ 100 μM；pIC50 = 6 − 该值。
- 亲和力是模型预测值，**不是实验测得的 Kd / IC50**；只针对一个配体
  （本任务的配体链）；口袋或姿态错了，数值再好看也没意义。详见报告里的
  “注意事项”一节。
- 亲和力限制：配体 ≤128 个重原子（作者建议 ≤56）；超过 128 只做结构，
  不计算亲和力。

## 发布到玻尔

见 [`bohrium/bohrium-publish.md`](bohrium/bohrium-publish.md)（清单 + `bohr` 命令），
App 元数据见 [`bohrium/app.json`](bohrium/app.json)。

核心模式：**我们只做应用、发布镜像；用户在玻尔上自己开 GPU 节点、用玻尔算力跑，
算力费由用户付给玻尔。** 本仓库不调用任何第三方 API（MSA 自动生成除外，
用的是公开 ColabFold 服务器），不含任何密钥。

## 文件清单

```
.
├── README.md                  本文件
├── Dockerfile                 任务镜像（CUDA 12.4 + Python 3.11 + boltz[cuda]==2.2.1，权重烤进镜像）
├── requirements-boltz2.txt    Boltz-2 运行时依赖（已钉版本）
├── requirements-launching.txt Launching 依赖（标准离线任务型镜像用）
├── run_boltz2.py              命令行封装：生成 YAML → 调 boltz predict → 解析 JSON → 中文报告
├── launching.py               DP-Launching 入口（标准离线任务型）
├── .dockerignore
├── examples/
│   ├── test_run.sh            本地验证脚本（无 GPU 可跑的检查）
│   ├── README.md              示例说明
│   └── kras-g12c-sotorasib/   KRAS G12C + 索托拉西布（序列、SMILES、示例 YAML、解析测试用 JSON）
└── bohrium/
    ├── bohrium-publish.md     发布清单 + bohr 命令
    └── app.json               App 元数据（中英描述、输入/输出 schema）
```

## 注意事项

- Boltz-2 只用 v2.2.1（代码与权重均为 MIT）。2.1 只走托管 API，不在
  MIT 发布范围内，本封装不用。
- 共价配体（如索托拉西布结合 KRAS G12C 的 Cys12）目前只按非共价处理：
  共价键约束只支持 CCD 配体，SMILES 输入不建共价键；示例仅用于
  共折叠与亲和力流程演示，解读时请留意这一点。
- 口袋约束为可选高级参数；不填时模型自行判断结合位置。
- 显存不足时 Boltz 可能仍以退出码 0 结束：封装只认输出文件是否存在，
  不认退出码；缺失时任务按失败处理并提示换更小结构或更大显存机型。

## 许可与引用

- Boltz-2 本身：MIT 许可。使用本 App 做科研请引用：
  - Passaro, S. et al. *Boltz-2: Towards Accurate and Efficient Binding Affinity
    Prediction.* bioRxiv (2025). doi:10.1101/2025.06.14.659707
- Boltz-2 代码与权重：https://github.com/jwohlwend/boltz，
  Hugging Face：`boltz-community/boltz-2`
- MSA 自动生成用 ColabFold 服务器时请引用：
  - Mirdita, M. et al. *ColabFold: making protein folding accessible to all.*
    Nat. Methods (2022).
- 本应用的封装代码与文档：随仓库发布，使用时请保留上述 Boltz-2 引用和许可说明。
