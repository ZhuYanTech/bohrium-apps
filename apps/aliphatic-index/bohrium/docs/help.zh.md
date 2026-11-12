## 选择一种输入

- **粘贴序列**：单条裸序列或多条 FASTA。裸序列的编号为 `Sequence`。
- **上传文件**：FASTA（`.fasta/.fa/.fas/.faa`）、TXT、CSV 或 PDB。CSV 使用 `id,sequence` 列，也接受 `name,seq`。PDB 读取首个模型有坐标的蛋白链；支持部分已知修饰残基，例如 MSE。
- **结构编号**：填写四位 RCSB PDB 编号以查询 FASTA。查询需要运行环境能访问 RCSB。

输入只接受 20 种标准氨基酸。字母大小写及空白不影响计算。任一空记录或非法残基会使整批报错。选择 CPU 后提交，无需设置算法参数。

## 样例与结果

粘贴 `AV IL` 可得到编号 `Sequence`、长度 4、指数 **292.50**。胰岛素示例见应用介绍。

`results.csv` 含编号、长度和两位小数的脂肪族指数。`aliphatic_index.csv` 另含 A、V、I、L 计数及六位小数的指数。两张表均按编号排序。

[开源实现与使用说明](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/aliphatic-index)
