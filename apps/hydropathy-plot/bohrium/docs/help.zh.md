## 输入、参数和结果

上传 FASTA/TXT/PDB、粘贴一条蛋白序列，或用 PDB 编号取 FASTA。多条序列请上传文件。窗口为 5 到 21 的奇数，默认 9。每个完整窗口的平均值放在中心残基位置，首尾无完整窗口的位置不报告。输入 MKTAYIAKQR，窗口设为 5，得到 6 个分数，首个为 −0.44。输出 CSV 和逐条序列的 PNG。

`hydropathy.csv` 按序列记录编号、中心位置、中心残基和得分。每条序列另有一张 `hydropathy_*.png`。对文档中的十残基样例，中心位置 3–8 的结果为 −0.44、0.08、1.22、0.58、−0.48、−1.12。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/hydropathy-plot) · [上游开源仓库](https://github.com/biopython/biopython)
