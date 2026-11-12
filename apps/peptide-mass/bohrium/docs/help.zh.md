## 输入、参数和结果

上传 FASTA/TXT、粘贴蛋白序列，或按 PDB 编号取 FASTA。可设酶切规则、0–5 次漏切、单同位素/平均质量、离子类型、固定半胱氨酸修饰、甲硫氨酸氧化、质量范围和排序。默认胰蛋白酶与 [M+H]⁺。输入 AKR，预期 AK 为 218.1499、R 为 175.1190。规则为序列层面的简化。

酶切代码可用 `trypsin`、`trypsin_all`、`lys_c`、`arg_c`、`asp_n`、`glu_c_phosphate`、`glu_c_bicarbonate`、`chymotrypsin`、`pepsin`、`proteinase_k`、`cnbr` 或 `formic_acid`。离子可用 `h`、`neutral`、`minus_h`、`2h` 或 `3h`。半胱氨酸修饰可用 `none`、`cam`、`cm`、`vp` 或 `acrylamide`。`peptides.csv` 的位置从 1 开始，质量和质荷比保留四位小数。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/peptide-mass)
