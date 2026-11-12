# 文本转 FASTA

上传纯文本、FASTA、CSV/TSV，或粘贴单行文本。表格使用 sequence 或 seq 列，可选 name 或 id。多条记录及换行文本请上传。支持自动、空行、合并和自定义分组，输出标题、大小写及换行宽度可设。校验方式为 lenient、strict 或 off。可保留缺口和终止符。输入 1 mkt ayia 后得到 MKTAYIA，run.log 记录跳过原因。Word 和 PDF 请先提取为文本。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t txt-to-fasta:1.0.0 .
docker run --rm --platform linux/amd64 txt-to-fasta:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/txt-to-fasta)
