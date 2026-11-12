# 蛋白结构 RMSD 计算

上传参考与待比较 PDB/mmCIF，或分别输入 PDB 编号。多个待比较结构可用 ZIP。默认使用 Cα、等权和首模型，先作 Kabsch 拟合。可分别设置拟合与测量原子和残基范围，按结构、链或显式链映射比较。原子按标识符对应。结果含总体及逐残基 CSV、变换 JSON 和可选拟合结构。同一 1UBQ 对比自身，Cα RMSD 约为 0 Å。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t rmsd-calculator:1.0.0 .
docker run --rm --platform linux/amd64 rmsd-calculator:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/rmsd-calculator) · [上游开源仓库](https://github.com/biopython/biopython)
