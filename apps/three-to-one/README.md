# 氨基酸三字母转单字母

上传 TXT/FASTA/SEQ 或粘贴单行三字母序列。多条记录请上传文件。支持自动、空格、连字符、逗号、制表符、分号和自定义分隔符。未知值可填 x、skip、error 或 bracket。可设大小写、保留 FASTA 标题及每行宽度。Cys-Tyr-Ile-Gln-Asn-Cys-Pro-Leu-Gly 输出 CYIQNCPLG。Word 和 PDF 请先转为文本。

使用 Docker 验证样例。

```sh
docker build --platform linux/amd64 -t three-to-one:1.0.0 .
docker run --rm --platform linux/amd64 three-to-one:1.0.0 bash examples/test_run.sh
```

[中文帮助](bohrium/docs/help.zh.md) · [English guide](bohrium/docs/help.en.md)

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/three-to-one)
