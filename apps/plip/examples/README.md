# examples/ — 示例与已验证结果

## test_run.sh

本地验证脚本，见文件内注释。用法：

```bash
bash examples/test_run.sh
# 指定 PLIP 可执行文件（例如 venv 里的）：
PLIP_CMD=plip bash examples/test_run.sh
```

它会跑 1VSN，并检查错误用例（不存在的文件、格式不对的 PDB ID、无配体 PDB）。

## verified-1vsn/ — 运行结果

PLIP 3.0.1 运行 `1VSN`（Cathepsin K + 小分子抑制剂 NFT）得到的结果，
由 `run_plip.py` 生成：

| 文件 | 说明 |
| --- | --- |
| `interactions.csv` | 13 行相互作用（表头 + 13 行） |
| `report_zh.md` | 中文报告 |
| `1VSN_report.xml` / `1VSN_report.txt` | PLIP 原始输出 |

计数（PLIP 3.0.1，模型 1，配体 NFT:A:283）：

| 类型 | 数量 |
| --- | ---: |
| 氢键 | 7 |
| 疏水相互作用 | 4 |
| 卤键 | 2 |
| 水桥 / 盐桥 / π-堆积 / π-阳离子 / 金属配位 | 0 |
| **合计** | **13** |

关键残基：ASP61（3 个）、TYR67（3 个）、GLY66（2 个）。

换 PLIP 版本后数字可能略有不同，以当场运行为准。

## verified-3mxf/ — 运行结果

PLIP 3.0.1 运行 `3MXF`（BRD4 + JQ1）得到的结果，由 `run_plip.py` 生成：

| 文件 | 说明 |
| --- | --- |
| `interactions.csv` | 27 行相互作用（表头 + 27 行） |
| `report_zh.md` | 中文报告 |
| `3MXF_report.xml` / `3MXF_report.txt` | PLIP 原始输出 |

**注意：27 是全部 HETATM 配体的合计，不是 JQ1 一个人的。** 3MXF 里除了
JQ1 还有结晶溶剂 DMS、EDO，PLIP 都算进去了。按配体拆分：JQ1 14 个
（疏水 11、水桥 2、氢键 1）、EDO 8 个、DMS 5 个。JQ1 的关键残基：
ASN140（经典氢键锚点）、ASP145、ILE146、TRP81、TYR97。报告按配体分开计数，
详见 `../VERIFICATION.md`。
