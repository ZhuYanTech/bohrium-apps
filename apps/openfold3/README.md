# OpenFold3 结构预测

输入蛋白序列（可加配体、DNA、RNA），预测生物大分子复合物的三维结构，
输出结构文件（CIF/PDB）、各样本置信度汇总与中文解读报告。

底层模型：OpenFold3 v0.5.0（Apache 2.0，代码与权重均可商用），
检查点 OpenBind-0（`of3-ob-2025-06-30-174k.pt`，约 2.29 GB），
构建时烤进镜像，运行时显式指定，不依赖默认检查点名。

## 输入

- 蛋白（单条链，三选一，必选其一）：粘贴序列 / PDB 编号（从 RCSB 取第一条链）/ PDB 文件上传（提取第一条链的序列）
- 配体（可选，三选一，至多一种）：SMILES / SDF 文件上传（镜像内用 OpenBabel 转 SMILES）/ PubChem 编号（运行时取标准 SMILES）
- DNA 序列（可选）、RNA 序列（可选）
- 残基修饰（可选）：`3:SEP,5:MHO`（位置:修饰代码，逗号分隔）
- 口袋约束（可选，仅用于含配体的任务）：`B|A:45,A:46|4.0`（配体链|蛋白链:残基,…|最大距离 Å）
- 自备 MSA（可选）：上传 `.a3m` 文件，指定后跳过自动生成；第一条序列须与输入蛋白一致
- 生成 MSA（默认开）：通过 ColabFold 服务器自动生成；关闭则为单序列模式，精度可能下降
- 使用模板（默认开）：用 ColabFold 模板搜索结果辅助预测
- 模型种子数 1–5（默认 1）、每种子扩散样本数 1–10（默认 5）
- 随机种子（可选，填了可复现）、输出格式 CIF（默认）/ PDB

## 输出

- `predicted.cif` / `predicted.pdb`：排名第一的预测结构
- `summary.csv`：各样本置信度汇总（按 `sample_ranking_score` 排序）
- `report_zh.md`：中文解读报告（pLDDT 分段、pTM/ipTM 解读、注意事项）
- `query.json`、`runner.yml`：生成的 OpenFold3 输入与配置，可复核、可直接拿去跑 `run_openfold predict`
- `openfold3_raw/`：OpenFold3 原生输出（各样本结构、置信度 JSON、MSA、timing）

## 本地运行（试运行，不预测）

```bash
bash examples/test_run.sh
python3 run_openfold3.py --protein-sequence-file examples/ubiquitin-1ubq/sequence.fasta \
    --out-dir /tmp/of3-test --dry-run
```

真实预测需要 GPU（24 GB 显存起步，32 GB 推荐）与已装 OpenFold3 0.5.0 的环境；
本机无 GPU 时只能做试运行校验。

## 镜像

```bash
docker build -t zhuyan-xlab/openfold3:1.0 .
```

Dockerfile 不含 COPY，可直接粘贴到玻尔镜像中心构建：
见 `bohrium/Dockerfile.imagehub`（与本目录的 `Dockerfile` 内容相同）。

## 文件

| 文件 | 说明 |
| --- | --- |
| `run_openfold3.py` | 命令行封装：生成输入、调用 `run_openfold predict`、汇总输出 |
| `launching.py` | 玻尔离线任务 Launching 封装 |
| `build.sh` | 镜像构建脚本（PyTorch、OpenFold3、OpenBabel、检查点、Launching SDK） |
| `Dockerfile` | 自包含镜像定义（无 COPY，从公开仓库克隆封装脚本） |
| `requirements-openfold3.txt` | `openfold3==0.5.0`（torch 另行安装，见 build.sh） |
| `requirements-launching.txt` | Launching SDK |
| `bohrium/app.json` | App 元数据（输入、输出、限制、引用） |
| `bohrium/Dockerfile.imagehub` | 粘贴到镜像中心的 Dockerfile 全文 |
| `bohrium-publish.md` | 发布步骤 |
| `examples/` | 测试用例：泛素 1UBQ 与示例置信度数据 |
| `VERIFICATION.md` | 校验说明 |

## 限制

- 单条蛋白链；配体、DNA、RNA 各至多一条。不支持离子链与环化肽：
  OpenFold3 的输入格式没有这两种输入项。
- 只预测结构与置信度，**不预测结合亲和力**。需要定量亲和力请用 Boltz-2。
- GPU 24 GB 显存起步，32 GB 推荐；蛋白上限 1600 个残基。
- MSA 通过 ColabFold 服务器自动生成（2–5 分钟），玻尔节点能否访问该服务器尚未确认；
  若无法访问，请关闭“生成 MSA”或上传自备 `.a3m`。
- 显存不足时 OpenFold3 可能仍以退出码 0 结束；本封装只认输出文件是否存在，
  无输出文件时报运行失败。

## 引用

- OpenFold Consortium. OpenFold3: A Fully Open Source Biomolecular Structure
  Prediction Model Based on AlphaFold3. https://github.com/aqlaboratory/openfold-3
- Abramson, J. et al. Accurate structure prediction of biomolecular interactions
  with AlphaFold 3. Nature (2024). doi:10.1038/s41586-024-07487-w
- MSA 自动生成用 ColabFold 服务器时请引用：Mirdita, M. et al. ColabFold:
  making protein folding accessible to all. Nat. Methods (2022).
