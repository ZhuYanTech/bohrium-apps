## PDB 转 FASTA

从 PDB 坐标或 SEQRES 记录提取各链序列并导出 FASTA。

结构的坐标记录与提交时的全长序列可能不同。选择坐标模式可提取可见残基，选择 SEQRES 可取得结构文件所列的完整链序列。支持蛋白质和核酸，输出可以交给接受 FASTA 的下游工具。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/pdb-to-fasta) · [上游开源仓库](https://github.com/biopython/biopython)
