# 蛋白质亲疏水性曲线

上传 FASTA/TXT/PDB、粘贴一条蛋白序列，或用 PDB 编号取 FASTA。多条序列请上传文件。窗口为 5 到 21 的奇数，默认 9。每个完整窗口的平均值放在中心残基位置，首尾无完整窗口的位置不报告。输入 MKTAYIAKQR，窗口设为 5，得到 6 个分数，首个为 −0.44。输出 CSV 和逐条序列的 PNG。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t hydropathy-plot:1.0.0 .
docker run --rm --platform linux/amd64 hydropathy-plot:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/hydropathy-plot) · [上游开源仓库](https://github.com/biopython/biopython)
