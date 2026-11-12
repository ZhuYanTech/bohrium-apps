# 溶剂可及表面积计算

上传 PDB、ENT、mmCIF 或多结构 ZIP，或填写 PDB 编号。探针半径填 1.4、1.8 或 2.0 Å。每个重原子采样 92 个点，输出残基、链和结构 CSV。相对可及性仅在 1.4 Å 下报告，链首末和没有参考值的残基留空。用 1UBQ 核对一条链、76 个残基和约 4,888 Å² 的总面积。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t sasa-calculator:1.0.0 .
docker run --rm --platform linux/amd64 sasa-calculator:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/sasa-calculator) · [上游开源仓库](https://github.com/biopython/biopython)
