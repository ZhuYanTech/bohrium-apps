## 输入、参数和结果

上传参考与待比较 PDB/mmCIF，或分别输入 PDB 编号。多个待比较结构可用 ZIP。默认使用 Cα、等权和首模型，先作 Kabsch 拟合。可分别设置拟合与测量原子和残基范围，按结构、链或显式链映射比较。原子按标识符对应。结果含总体及逐残基 CSV、变换 JSON 和可选拟合结构。同一 1UBQ 对比自身，Cα RMSD 约为 0 Å。

范围可写成 `1:76,80`。打开全部模型时，每个模型对单独输出。`rmsd.csv` 包含覆盖率、拟合原子数和位移，`per_residue.csv` 是逐残基结果，`rmsd_transformations.json` 保存旋转和平移。用 1UBQ 对比 1D3Z，默认设置下首模型 76 个 Cα 对应，约 0.5214 Å。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/rmsd-calculator) · [上游开源仓库](https://github.com/biopython/biopython)
