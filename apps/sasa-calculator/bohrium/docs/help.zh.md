## 输入、参数和结果

上传 PDB、ENT、mmCIF 或多结构 ZIP，或填写 PDB 编号。探针半径填 1.4、1.8 或 2.0 Å。每个重原子采样 92 个点，输出残基、链和结构 CSV。相对可及性仅在 1.4 Å 下报告，链首末和没有参考值的残基留空。用 1UBQ 核对一条链、76 个残基和约 4,888 Å² 的总面积。

`residues.csv` 给出逐残基面积和暴露分级，`chains.csv` 与 `summary.csv` 汇总。相对可及性低于 20% 为埋藏，高于 50% 为暴露，中间为过渡。链首末或无参考面积的残基留空并给出原因。1UBQ 的 1.4 Å 结果为 4,888.35 Å²，1.8 Å 结果为 4,837.27 Å²。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/sasa-calculator) · [上游开源仓库](https://github.com/biopython/biopython)
