## 输入、参数和结果

上传纯文本、FASTA、CSV/TSV，或粘贴单行文本。表格使用 sequence 或 seq 列，可选 name 或 id。多条记录及换行文本请上传。支持自动、空行、合并和自定义分组，输出标题、大小写及换行宽度可设。校验方式为 lenient、strict 或 off。可保留缺口和终止符。输入 1 mkt ayia 后得到 MKTAYIA，run.log 记录跳过原因。Word 和 PDF 请先提取为文本。

默认自动分组、自动类型、保留可识别标题、转大写且不换行。需要合并一段没有标题的序列时选 `join`。自定义分组需填分隔符。表格文件的序列列为 `sequence` 或 `seq`。下载 `sequences.fasta` 与 `run.log`，对照记录数和被跳过的行。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/txt-to-fasta)
