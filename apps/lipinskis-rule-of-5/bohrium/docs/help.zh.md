## 输入、参数和结果

上传 SMI、SMILES、TXT、CSV 或 TSV，或粘贴单条 SMILES。CSV/TSV 可使用 smiles 和 name/id 列。分别以 500 Da、5、5 和 10 为上限，零或一项偏离标为通过。无效 SMILES 单独标记，其他分子仍计算。阿司匹林预期 180.16 Da、LogP 1.31、供体 1、受体 3。筛查结果不能替代实验吸收数据。

`lipinski.csv` 保留分子名称和 SMILES，给出四项计算值、偏离数、判定和解析状态。分子量与 LogP 阈值分别为 500 Da 与 5，供体和受体阈值分别为 5 和 10。CSV 批量运行中，无效行保留其解析状态。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/lipinskis-rule-of-5) · [上游开源仓库](https://github.com/rdkit/rdkit)
