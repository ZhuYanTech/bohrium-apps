## 输入、参数和结果

上传 PDB/ENT 或输入四位 PDB 编号。序列来源填 observed 或 seqres，分子类型填 all、protein 或 nucleic。链号用逗号分隔，留空表示全部。编号间缺口可插入蛋白 X 或核酸 N。可包含已知修饰残基。标题填 id_chain、title_chain 或 chain。每行宽度为 0、60、80 或 100。用 1UBQ 可得到 A 链 76 个残基。

`sequences.fasta` 每条链一个记录。默认取坐标、保留可识别修饰残基、每行 80 个字符。选择 `seqres` 时读取文件自身的 SEQRES 记录。要得到 1UBQ 的 A 链短标题及 60 字符换行，填写链 A，标题填 `chain`，宽度填 60。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/pdb-to-fasta) · [上游开源仓库](https://github.com/biopython/biopython)
