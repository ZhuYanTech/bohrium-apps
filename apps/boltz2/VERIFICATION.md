# 验证结果

Boltz-2 v2.2.1（`boltz[cuda]==2.2.1`，cuEquivariance 0.6.1）。
无 GPU 可跑的检查：`bash examples/test_run.sh`（26 项全过）。

## 已验证（无 GPU）

- 输入验证：空序列、非法字符、超过 2900 个残基、SMILES 非法、SMILES 与 CCD
  同时提供、`.a3m` 与 `--no-msa` 同时提供，均以退出码 2 优雅失败，中文报错。
- YAML 生成：`--dry-run` 生成 `input.yaml`，含蛋白链、配体 SMILES、
  亲和力 `binder: B`；三种 MSA 分支（自动生成 / 上传 `.a3m` / 单序列）
  生成的 YAML 各不相同且符合 Boltz 输入格式。
- 重原子计数：索托拉西布 41 个（≤56，无警告）；超过 128 个重原子的配体
  自动只做结构、不计算亲和力。
- 输出解析：解析测试用的置信度/亲和力 JSON（官方文档示例值）生成中文报告，
  含换算表与注意事项。
- 输出收集：按 Boltz 2.2.1 的真实目录 `boltz_results_<stem>/predictions/<stem>/`
  收集输出（旧 `predictions/<stem>/` 仅作回退）。
- DP-Launching 入口：`launching.py -p` 生成 JSON Schema（退出码 0）；
  `--json-config` 试运行（dry_run）生成 YAML（退出码 0）；
  既不填序列也不填配体时退出码 1，中文提示。

## 示例：KRAS G12C + 索托拉西布

见 `examples/kras-g12c-sotorasib/`：KRAS G12C 序列（UniProt P01116，
Gly12→Cys，共 189 个残基）、索托拉西布 SMILES（PubChem CID 137278711，
C30H30F2N6O3，重原子 41 个）。在 Colab T4（16 GB）上实际预测成功：
结合概率 0.885，预测亲和力 -0.876（log10 IC50 μM，约 133 nM），
confidence_score 0.9131，pLDDT 0.8963，ipTM 0.9802；MSA 由 ColabFold
服务器自动生成；峰值显存约 9.9 GB。索托拉西布是共价抑制剂，
SMILES 输入按非共价处理，亲和力数值仅作流程演示。

## 未验证（需玻尔环境）

- Docker 镜像构建：`docker build` 未跑过（镜像约 7 GB，含 6.2 GB 权重）。
- 权重烤进镜像的步骤：Hugging Face 下载与缓存目录布局，需在首次构建时核对。
- 玻尔节点能否访问公开 ColabFold MSA 服务器（api.colabfold.com）：
  Colab 上可达；玻尔节点尚未验证，若不能，默认自动生成 MSA 不可用，
  需改传 `.a3m`。
- 玻尔发布与上架后验收。
