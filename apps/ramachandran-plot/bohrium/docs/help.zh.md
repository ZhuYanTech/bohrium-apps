## 输入、参数和结果

上传 PDB、ENT 或 mmCIF，或填写四位 PDB 编号。只分析第一个模型中具备完整、相连主链的残基。输出拉氏图 PNG 及逐残基 CSV。参考表使用 2° 网格，靠近边界时分类可能不同于插值方法。可用 1UBQ 验证，预期至少有 70 个可测残基，φ 和 ψ 在 −180° 至 180°。

`ramachandran.csv` 包含链、残基编号、参考类别、角度、参考密度及分类，`ramachandran.png` 绘制分布和观测点。密度至少 0.02 为优选。允许区的下限分别为一般类 0.0005、顺式脯氨酸 0.002，其余四类 0.001。低于相应下限标为离群。1UBQ 的 mmCIF 验收样例有 74 个可测残基。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/ramachandran-plot) · [上游开源仓库](https://github.com/rlabduke/rotarama_data)
