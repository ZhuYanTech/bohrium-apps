# 酶切肽段质量计算

上传 FASTA/TXT、粘贴蛋白序列，或按 PDB 编号取 FASTA。可设酶切规则、0–5 次漏切、单同位素/平均质量、离子类型、固定半胱氨酸修饰、甲硫氨酸氧化、质量范围和排序。默认胰蛋白酶与 [M+H]⁺。输入 AKR，预期 AK 为 218.1499、R 为 175.1190。规则为序列层面的简化。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t peptide-mass:1.0.0 .
docker run --rm --platform linux/amd64 peptide-mass:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/peptide-mass)
