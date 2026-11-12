# PDB 转 FASTA

上传 PDB/ENT 或输入四位 PDB 编号。序列来源填 observed 或 seqres，分子类型填 all、protein 或 nucleic。链号用逗号分隔，留空表示全部。编号间缺口可插入蛋白 X 或核酸 N。可包含已知修饰残基。标题填 id_chain、title_chain 或 chain。每行宽度为 0、60、80 或 100。用 1UBQ 可得到 A 链 76 个残基。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t pdb-to-fasta:1.0.0 .
docker run --rm --platform linux/amd64 pdb-to-fasta:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/pdb-to-fasta) · [上游开源仓库](https://github.com/biopython/biopython)
