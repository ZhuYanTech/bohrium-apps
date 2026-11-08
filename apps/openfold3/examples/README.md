# 示例

## 泛素 1UBQ

标准测试用例：泛素（76 个残基，PDB 编号 1UBQ），单条蛋白链。

- `sequence.fasta`：泛素序列（RCSB FASTA）
- `ubiquitin-seqres.pdb`：SEQRES 形式的 PDB 文件（测试 PDB 文件提取）
- `tiny-atom.pdb`：只有 3 个 CA 原子的 PDB 文件（测试 ATOM 提取路径）
- `ethanol.sdf`：乙醇 SDF 文件（测试 SDF → SMILES 转换，应得 `CCO`）
- `ubiquitin.a3m`：示例 MSA（第一条序列与输入蛋白一致；测试自备 MSA）
- `canned/`：示例置信度数据（见其中 README），用于测试解析逻辑，
  **不是**本 App 的真实运行结果

## 运行测试

```bash
bash examples/test_run.sh
```

测试只做输入生成、参数映射与输出解析，不做真实预测（无 GPU 时也能跑）。
