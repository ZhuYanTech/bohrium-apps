# 验证结果

PLIP 3.0.1（openbabel 3.2.1、numpy 2.5.4、lxml 6.1.3）。复现：`bash examples/test_run.sh`（9 项检查）。

## 1VSN（Cathepsin K + NFT）

13 个相互作用：氢键 7、疏水 4、卤键 2。关键残基 ASP61（3）、TYR67（3）、GLY66（2）。

输出见 `examples/verified-1vsn/`：`interactions.csv`、`report_zh.md`、PLIP 原始 XML/TXT。

## 3MXF（BRD4 + JQ1）

全部配体合计 27 个：JQ1 14 个（疏水 11、水桥 2、氢键 1）、EDO 8 个、DMS 5 个。
JQ1 关键残基 ASN140、ASP145、ILE146、TRP81、TYR97。

`--ligand JQ1` 或 `--exclude-solvents` 均为 14 行。

输出见 `examples/verified-3mxf/`：`interactions.csv`、`report_zh.md`、PLIP 原始 XML/TXT。

## 错误用例

| 输入 | 退出码 | 结果 |
| --- | ---: | --- |
| 不存在的 PDB 文件 | 2 | 中文报错“PDB 文件不存在” |
| 格式不对的 PDB ID（如 `XYZ`） | 2 | 中文报错“PDB ID 格式不对（应为 4 位，如 1VSN）” |
| 只有蛋白原子的 PDB（无 HETATM 配体） | 0 | 空表（0 行）+ 中文报告说明“未检测到相互作用” |

## DP-Launching 入口

`python launching.py --json-config <config>`：PDB ID `1VSN` 得 13 个相互作用，
`interactions.csv` 与 `examples/verified-1vsn/interactions.csv` 相同；
既不传 PDB 文件也不传 PDB 编号时退出码 1，中文提示二选一。

## Streamlit 界面

启动后首页 HTTP 200，`/_stcore/health` 返回 ok。
