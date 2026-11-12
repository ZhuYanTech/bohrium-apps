# Lipinski 五规则

上传 SMI、SMILES、TXT、CSV 或 TSV，或粘贴单条 SMILES。CSV/TSV 可使用 smiles 和 name/id 列。分别以 500 Da、5、5 和 10 为上限，零或一项偏离标为通过。无效 SMILES 单独标记，其他分子仍计算。阿司匹林预期 180.16 Da、LogP 1.31、供体 1、受体 3。筛查结果不能替代实验吸收数据。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t lipinskis-rule-of-5:1.0.0 .
docker run --rm --platform linux/amd64 lipinskis-rule-of-5:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/lipinskis-rule-of-5) · [上游开源仓库](https://github.com/rdkit/rdkit)
