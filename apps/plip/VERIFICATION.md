# 验证记录（VERIFICATION）

日期：2026-11-07
环境：Python 3.12，PLIP 3.0.1（`pip install plip==3.0.1`，含 openbabel 3.2.1、
numpy 2.5.4、lxml 6.1.3）。Docker 镜像构建尚未验证。

## 1. PLIP 安装（真实执行）

```bash
pip install plip==3.0.1
plip --help
# 输出：PLIP Version 3.0.1，含 --model、-x/-t/-y/-p 等选项
```

## 2. PLIP 原生运行：1VSN（真实执行）

```bash
curl -sL -o 1vsn.pdb https://files.rcsb.org/download/1VSN.pdb   # 188,811 字节
plip -f 1vsn.pdb -o out -xtv
# 退出码 0，生成 1vsn_report.xml（15,651 字节）、1vsn_report.txt（7,751 字节）
# 注意：加 -y/-p 时报错 "PyMOL is required for the --pics and --pymol option"，
# 因此封装默认不传 -y/-p（见 README 注意事项）。
```

XML 解析计数（`bindingsite id=1`，配体 NFT:A:283）：

| 类型 | 数量 |
| --- | ---: |
| 氢键 hydrogen_bonds | 7 |
| 疏水相互作用 hydrophobic_interactions | 4 |
| 卤键 halogen_bonds | 2 |
| 水桥 / 盐桥 / π-堆积 / π-阳离子 / 金属配位 | 0 |
| **合计** | **13** |

关键残基：ASP61（3）、TYR67（3）、GLY66（2）。

## 3. 封装 run_plip.py 运行：1VSN（真实执行）

```bash
# PDB 文件先从 RCSB 下载（https://files.rcsb.org/download/1VSN.pdb），
# 用相对路径传入：原始 XML 里只记录文件名，不含本机路径。
python run_plip.py --pdb-file 1VSN.pdb --out-dir ./plip-output
# 输出：“完成：共 13 个相互作用，氢键 7；疏水相互作用 4；卤键 2”
# 生成：interactions.csv（13 行 + 表头）、report_zh.md、plip_raw/
```

修复记录：首次运行因 f-string 嵌套引号报 SyntaxError，已修复（把配体描述
抽成单独变量），修复后 `python3 -m py_compile run_plip.py app_streamlit.py` 通过。

## 4. 错误用例（真实执行，直接测退出码，不经管道）

| 用例 | 退出码 | 表现 |
| --- | --- | --- |
| `--pdb-file /tmp/nope.pdb`（不存在） | 2 | 中文报错“PDB 文件不存在” |
| `--pdb-id XYZ`（格式不对） | 2 | 中文报错“PDB ID 格式不对（应为 4 位，如 1VSN）” |
| 只有蛋白原子的 PDB（无 HETATM 配体） | 0 | 生成空表（0 行）+ 中文报告说明“未检测到相互作用”，不崩溃 |

## 5. 一键测试脚本（真实执行）

```bash
bash examples/test_run.sh
# 结果：通过 9，失败 0（SCRIPT_EXIT 0）
# 覆盖：1VSN 主用例（5 项）、不存在文件（1 项）、PDB ID 格式（1 项）、
#       无配体（2 项）
```

## 6. 其他检查（真实执行）

- `python3 -m json.tool bohrium/app.json`：合法 JSON。
- `python3 -m py_compile run_plip.py app_streamlit.py`：通过。
- `examples/verified-1vsn/`：从第 3 步的真实输出复制而来（CSV/报告/XML/TXT），
  未做任何手工改动。

## 7. 第二个标准例子：3MXF（BRD4 + JQ1，真实执行）

```bash
# PDB 文件先从 RCSB 下载，用相对路径传入（同第 3 节）。
python run_plip.py --pdb-file 3MXF.pdb --out-dir ./plip-output-3mxf
# 退出码 0。输出：“完成：共 27 个相互作用，疏水相互作用 11；氢键 9；水桥 5；盐桥 2”
# 生成：interactions.csv（27 行 + 表头）、report_zh.md、plip_raw/
```

真实输出已原样存入 `examples/verified-3mxf/`（CSV/报告/原始 XML/TXT），未手工改动。

**重要发现——27 这个总数会误导，JQ1 本身只有 14 个：**
3MXF 的 PDB 里除了 JQ1，还有结晶溶剂 DMS、EDO（也是 HETATM），PLIP
把它们都当配体算了。按配体拆分（直接数 `interactions.csv` 的 ligand 列）：

| 配体 | 数量 |
| --- | ---: |
| JQ1（目标抑制剂） | 14（疏水 11、水桥 2、氢键 1） |
| EDO（溶剂） | 8 |
| DMS（溶剂） | 5 |
| **合计** | **27** |

JQ1 的关键残基与文献一致：ASN140（经典氢键锚点）、ASP145、ILE146、
TRP81、TYR97、LEU94、PHE83、PRO82、LEU92、VAL87。

**对 v1 的改进建议（已做，见第 9 节）：** 报告里应按配体分开计数，
或默认过滤 DMS/EDO 这类常见溶剂、让用户选要分析哪个配体，否则用户
看到“27 个相互作用”会以为都是药物的。玻尔 App 上架前做这一步。

## 8. Streamlit 界面启动验证（真实执行）

```bash
pip install -r requirements.txt   # streamlit + pandas
streamlit run app_streamlit.py \
  --server.headless true --server.port 8502 --server.address 127.0.0.1
# curl http://127.0.0.1:8502/ → HTTP 200
# curl http://127.0.0.1:8502/_stcore/health → "ok"，HTTP 200
# 日志里无 error / traceback / exception；验证后已停掉服务（curl 确认已停）
```

限定：只验证了服务能启动、HTTP 200、健康检查 ok；界面内容是
Streamlit 客户端渲染的，未在浏览器里逐项点过（上传 PDB、点分析按钮
仍需在浏览器里点一次）。

## 9. 按配体分开计数（真实执行，修复第 7 节的计数问题）

改动（`run_plip.py`，默认不丢数据）：
- 报告新增“按配体统计”一节：每个配体一行，标明是不是常见结晶溶剂；
  多配体且含溶剂时加一句警告（27 个里 13 个来自溶剂）。
- 新增 `--ligand <配体名>`（只分析该配体，不存在时退出码 2 并列出本结构
  检测到的配体）和 `--exclude-solvents`（过滤 DMS/EDO/GOL 等常见溶剂）。
- 默认仍保留全部配体：CSV 还是 27 行，原始 XML/TXT 不动。

实测（PLIP 3.0.1）：
- 3MXF 默认：27 行，控制台“按配体：JQ1 14 个；EDO 8 个；DMS 5 个”，
  报告含按配体表和溶剂警告；`examples/verified-3mxf/` 已用这次真实输出刷新。
- 3MXF `--ligand JQ1`：14 行；`--exclude-solvents`：14 行。
- 1VSN 默认：仍 13 行（NFT），无回归。
- 未知配体 `--ligand XXX`：退出码 2，报错“未找到配体 XXX。本结构检测到的
  配体：DMS, EDO, JQ1。”，不写 CSV。
- `bash examples/test_run.sh`：通过 9，失败 0。

## 10. DP-Launching 入口验证（真实执行）

`launching.py`（标准离线任务型 App 的入口，见 `launching.py` 注释）已用
真实的 `dp-launching-app 0.1.0a1` + `bohrium-open-sdk 1.0.5` + PLIP 3.0.1
实测通过：

- `python launching.py -p`：退出码 0，返回 schema 预览链接。
- `--json-config` 传 `{"pdb_id": "1VSN", "model": 1, "output_dir": "<输出目录>"}`：
  退出码 0，**13 个相互作用**（氢键 7、疏水 4、卤键 2），`interactions.csv`
  与 `examples/verified-1vsn/interactions.csv` 逐字节相同。
- `--json-config` 传 PDB 文件 + `"ligand": "NFT"`：退出码 0，13 行。
- `--json-config` 既不传文件也不传 PDB 编号：退出码 1，中文提示
  “请上传一个 PDB 文件，或输入一个 PDB 编号（二选一）。“
- `bash examples/test_run.sh`：通过 9，失败 0，无回归。

未验证：玻尔平台上真实上传文件的 `InputFilePath` 填充方式、预览链接在
开发者中心的渲染效果；须在玻尔上建版本实测。

## 未验证 / 明确未做的事

- **Docker 镜像构建未验证**：`docker build` 未跑过。Dockerfile 用的是
  `python:3.12-slim + pip install plip==3.0.1`，与本地验证同版本，但镜像内
  构建仍需在有 Docker 的机器上跑一次。
- **玻尔发布未做**：未登录、未推送镜像。`bohr` 命令、`project-id` 均为占位，
  见 `bohrium/bohrium-publish.md`，须发布者本人完成。
- **未调用任何第三方 API**：脚手架里没有任何外部 API 调用和密钥。
