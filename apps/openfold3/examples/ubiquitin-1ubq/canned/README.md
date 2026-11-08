# 示例置信度数据

本目录的三个 `*_confidences_aggregated.json` 是**示例数据**：
数值按 OpenFold3 的 `confidences_aggregated.json` 字段格式手写，
仅用于测试 `run_openfold3.py` 的解析逻辑（排序、CSV、报告生成），
**不是**本 App 的真实运行结果，也不是任何官方运行的输出。

- 种子 42，样本 1–3；样本 2 的 `sample_ranking_score` 最高（0.79），
  用于验证汇总按排序分从高到低排列。
- 单条蛋白链的示例，因此 `iptm` 为 0.0（无界面可评）；`chain_pair_iptm` 与
  `bespoke_iptm` 为空。含配体/DNA/RNA 的复合物示例中这两个字段才有值。
- 样本 3 的 `has_clash` 为 1.0，用于验证冲突标记能进报告。
