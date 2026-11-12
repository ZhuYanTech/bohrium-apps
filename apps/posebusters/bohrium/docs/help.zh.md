## 选择单文件或批量输入

- **单文件**：预测姿势必填。预测姿势、晶体参考与受体均可上传 SDF、MOL、MOL2 或 PDB。也可用四位 PDB 编号获取受体，同时填写时以上传文件为准。
- **批量**：上传 ZIP，内置 `mol_pred/`、可选 `mol_true/` 和 `mol_cond/`。每组按 ZIP 中条目顺序从 1 编号。一个参考和一个受体可共享给全部姿势。需要逐行配对时，在 ZIP 根目录放 `pairs.csv` 或在表单粘贴 CSV。列名为 `mol_pred,mol_true,mol_cond`，后两列可留空。
- 默认保留受体原样。只在需要时指定要移除的 PDB 配体残基名或打开自动识别。配体剥离会改变空间相容性检查。

## 验证模式与输出

可按输入自动选择，或手选 mol、dock、redock、regen、gen 及其快速模式。选 custom 时上传包含 `modules` 的完整 JSON。前 N 个姿势按每个预测文件计算；自定义配置明确指定 `top_n` 时以配置为准。

原生报告可选 Short、Long 或 CSV。所有模式保留 `results.csv`、`summary.csv`、`report_zh.md` 和版本、模式等运行元数据。批量模式另有逐配对目录。详细报告将额外诊断写入 CSV。汇总分别显示通过、未通过和未评估，只有全部预期检查通过才标为 PB-valid。

## 验证样例

使用内置的 1IA1 晶体配体作预测和参考，配上已移除该配体的受体，在 redock 模式预期通过 **28/28** 项。RMSD 阈值只用于参考姿势比较。

[上游开源仓库](https://github.com/maabuu/posebusters) · [玻尔封装与部署](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)
