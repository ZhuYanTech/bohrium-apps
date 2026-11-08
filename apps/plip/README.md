# PLIP 结合模式解析 — 玻尔（Bohrium）App

> 本 App 是 [`bohrium-apps`](https://github.com/ZhuYanTech/bohrium-apps) 单一仓库中的应用，位于 `apps/plip/`。
> 以下命令均在 `apps/plip/` 目录内执行。

上传蛋白-配体复合物 PDB 文件，或输入 PDB 编号，分析氢键、疏水、卤键、
盐桥、π-堆积等非共价相互作用，输出相互作用清单（CSV）和中文解读报告。

## 特点

- 分析型工具：对蛋白-配体复合物做相互作用分析，与结构预测工具互补。
- 轻：纯 CPU，不用 GPU，单结构通常 5 分钟内完成。
- PLIP 为 GPLv2，引用清楚就能用。
- 适用：对接、晶体结构解析后分析结合模式。

## 输入 / 输出

| | 内容 |
| --- | --- |
| 输入 | PDB 文件（须含 HETATM 配体），或 PDB ID（4 位，如 `1VSN`、`3MXF`，自动从 RCSB 下载）；可选模型编号，默认 1 |
| 输出 | `interactions.csv`（每行一个相互作用）、`report_zh.md`（中文报告：按类型计数、关键残基 Top 10）、`plip_raw/`（PLIP 原始 XML/TXT）、`images/`（如有 PNG 则在此，默认不生成） |

## 本地运行（不用玻尔账号也能试）

```bash
# 1. 装 PLIP（任选一种）
pip install plip==3.0.1          # 含 openbabel wheel；Python 3.10+
# 或用 Docker（见下）

# 2. 跑一个例子：1VSN，Cathepsin K + 抑制剂 NFT
python3 run_plip.py --pdb-id 1VSN --out-dir ./plip-output

# 3. 看结果
cat plip-output/report_zh.md
head plip-output/interactions.csv
```

（PLIP 3.0.1）1VSN：**13 个相互作用——氢键 7、疏水 4、卤键 2**，
关键残基 ASP61（3 个）、TYR67（3 个）。详见 `examples/verified-1vsn/`。

3MXF（BRD4 + JQ1）：全部配体合计 27 个，JQ1 本身
14 个（疏水 11、水桥 2、氢键 1，含 ASN140 经典氢键），其余 13 个是结晶溶剂
DMS、EDO 的。报告按配体分开计数（`report_zh.md` “按配体统计”一节，
并提示溶剂占比），详见 `examples/verified-3mxf/` 和 `VERIFICATION.md`。
Streamlit 界面：启动后首页 HTTP 200、健康检查 ok。

```bash
# 只看目标配体 JQ1（14 个），或过滤全部常见结晶溶剂
python3 run_plip.py --pdb-id 3MXF --ligand JQ1 --out-dir ./plip-output-jq1
python3 run_plip.py --pdb-id 3MXF --exclude-solvents --out-dir ./plip-output-nosolv
# 默认不丢数据：CSV 保留全部 27 个，报告按配体分开计数并标出溶剂
```

```bash
# 一键验证（含错误用例）
bash examples/test_run.sh
# 指定 PLIP 可执行文件：
PLIP_CMD=plip bash examples/test_run.sh
```

## 如何解读结果

- `interactions.csv`：每行一个相互作用——类型（中英）、配体、残基（链 + 编号）、
  距离、详细参数（供体/受体、角度等）。
- `report_zh.md`：按类型计数、关键残基 Top 10、按配体统计、注意事项。
- 个数不是亲和力：相互作用多 ≠ 结合强。只用于看结合模式、找关键残基、对照构效关系。
- 溶剂：结晶溶剂（DMS、EDO 等）也会被算进去。报告按配体分开计数并标出溶剂占比；
  只看目标配体时用 `--ligand` 或 `--exclude-solvents`。
- 水桥、盐桥、π-堆积、卤键的判定用 PLIP 默认距离/角度阈值，详见 PLIP 文档。

## 常见问题

- 任务失败 / 无报告：多半是 PDB 里没有配体（HETATM），或文件损坏；先在本地跑
  `bash examples/test_run.sh` 对照。
- 0 个相互作用：结构里可能没有配体，或配体离蛋白太远；检查 HETATM 记录和配体三字母代码。
- 个数和文献对不上：先看是不是溶剂被算进去了（见上）；再看模型编号（多模型 PDB
  默认只取模型 1）和 PLIP 版本。
- 没有 PNG 图片：正常。`-y`/`-p` 需要 PyMOL，本镜像没装；3D 查看请用 PyMOL 或
  Mol* 打开原 PDB。
- 多模型 PDB（如 NMR）：默认只分析模型 1，改模型编号可换模型。

## Docker 运行

```bash
docker build -t plip-bohrium-app:1.0 .
docker run --rm -v "$PWD:/work" plip-bohrium-app:1.0 \
  --pdb-id 1VSN --out-dir /work/plip-output
```

## 中文演示界面（Streamlit，仅演示用）

```bash
pip install -r requirements.txt   # streamlit + pandas
pip install plip==3.0.1
streamlit run app_streamlit.py
```

界面只调本机的 `run_plip.py`，不调任何外部 API。真正跑任务的是 `run_plip.py`。

## 发布到玻尔

见 [`bohrium/bohrium-publish.md`](bohrium/bohrium-publish.md)（清单 + `bohr` 命令），
App 元数据见 [`bohrium/app.json`](bohrium/app.json)。玻尔注册镜像名：
`zhuyan/plip-bohrium-app:1.0`。

核心模式：**我们只做应用、发布镜像；用户在玻尔上自己开节点、用玻尔算力跑，
算力费由用户付给玻尔。** 本仓库不调用任何第三方 API，不含任何密钥。

## 文件清单

```
.
├── README.md                  本文件
├── USER_GUIDE.md              使用指南（与开发者中心 User Guide 栏内容一致）
├── Dockerfile                 任务镜像（python:3.12-slim + plip==3.0.1）
├── requirements-plip.txt      PLIP 运行时依赖（已钉版本）
├── requirements.txt           Streamlit 演示界面依赖
├── run_plip.py                命令行封装：调 PLIP → 解析 XML → CSV + 中文报告
├── app_streamlit.py           中文演示界面（Streamlit）
├── .dockerignore
├── examples/
│   ├── test_run.sh            本地验证脚本（9 项检查）
│   ├── README.md              示例说明
│   ├── verified-1vsn/         1VSN 运行结果（CSV/报告/原始 XML/TXT）
│   └── verified-3mxf/         3MXF 运行结果（同上，含按配体分开的报告）
└── bohrium/
    ├── bohrium-publish.md     发布清单 + bohr 命令
    └── app.json               App 元数据（中英描述、输入/输出 schema）
```

## 注意事项

- PLIP 只检测“有什么相互作用”，**不预测结合亲和力**（Kd / ΔG），不要把
  相互作用个数直接当成亲和力高低。
- 默认不生成 PNG / PyMOL 会话文件，因为 `-y`/`-p` 需要 PyMOL，本镜像故意
  没装（镜像更小、构建更快）。3D 查看请用 PyMOL 或 Mol* 打开原 PDB。
- 距离、角度阈值用 PLIP 默认值。

## 许可与引用

- PLIP 本身：GNU GPLv2。使用本 App 做科研请引用：
  - Salentin, S. et al. *PLIP: fully automated protein-ligand interaction profiler.*
    Nucleic Acids Res. 43 (W1), W443–W447 (2015). doi:10.1093/nar/gkv315
  - Schake, P., Bolz, S. N. et al. *PLIP 2025: introducing protein–protein interactions
    to the protein–ligand interaction profiler.* Nucleic Acids Res. (2025), gkaf361.
    doi:10.1093/nar/gkaf361
- PLIP 代码与官方镜像：https://github.com/pharmai/plip，Docker Hub：`pharmai/plip`
- 本应用的封装代码与文档：随仓库发布，使用时请保留上述 PLIP 引用和许可说明。
