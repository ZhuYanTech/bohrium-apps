# examples/ — 示例与验证说明

## test_run.sh

本地验证脚本，见文件内注释。无 GPU 也能跑（只做输入验证、YAML 生成、
输出解析、Launching 入口检查，不实际预测）。用法：

```bash
bash examples/test_run.sh
# 指定 Boltz 可执行文件（例如容器里的）：
BOLTZ_CMD=boltz bash examples/test_run.sh
```

## kras-g12c-sotorasib/ — 示例输入

KRAS G12C + 索托拉西布（共价 KRAS G12C 抑制剂）：

| 文件 | 说明 |
| --- | --- |
| `sequence.txt` | KRAS G12C 序列，共 189 个残基。来源：UniProt P01116（KRAS_HUMAN），第 12 位 Gly→Cys |
| `ligand.smi` | 索托拉西布 SMILES。来源：PubChem CID 137278711，分子式 C30H30F2N6O3，重原子 41 个 |
| `kras-g12c.a3m` | 与序列一致的 `.a3m`（单条序列），用于测试 `--msa-file` 分支 |
| `input.yaml` | `run_boltz2.py --dry-run` 生成的 Boltz 输入（默认设置） |
| `canned/` | 解析测试用的置信度/亲和力 JSON（Boltz 官方文档示例值，非本 App 运行结果） |

试运行（只生成 YAML，不预测）：

```bash
python3 run_boltz2.py \
  --sequence-file examples/kras-g12c-sotorasib/sequence.txt \
  --ligand-smiles "$(cat examples/kras-g12c-sotorasib/ligand.smi)" \
  --out-dir ./boltz2-output --dry-run
```

GPU 上实际预测（需 24 GB 以上显存）：

```bash
python3 run_boltz2.py \
  --sequence-file examples/kras-g12c-sotorasib/sequence.txt \
  --ligand-smiles "$(cat examples/kras-g12c-sotorasib/ligand.smi)" \
  --out-dir ./boltz2-output
```

注意：索托拉西布是共价抑制剂（丙烯酰胺弹头结合 Cys12），本封装 v1
只按非共价处理——共价键约束只支持 CCD 配体，SMILES 输入不建共价键。
示例仅用于共折叠与亲和力流程演示，解读时请留意这一点。
