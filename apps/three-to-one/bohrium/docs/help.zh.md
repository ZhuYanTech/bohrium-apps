## 输入、参数和结果

上传 TXT/FASTA/SEQ 或粘贴单行三字母序列。多条记录请上传文件。支持自动、空格、连字符、逗号、制表符、分号和自定义分隔符。未知值可填 x、skip、error 或 bracket。可设大小写、保留 FASTA 标题及每行宽度。Cys-Tyr-Ile-Gln-Asn-Cys-Pro-Leu-Gly 输出 CYIQNCPLG。Word 和 PDF 请先转为文本。

默认自动识别空白、逗号和连字符，未知代码转 X，保留 FASTA 标题并输出大写。使用 `custom`、分隔符 `/` 和未知策略 `bracket` 时，`Ala/unknown/Arg` 得到 `A[unknown]R`。结果见 `converted.txt`，未知代码计数见 `run.log`。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/three-to-one)
