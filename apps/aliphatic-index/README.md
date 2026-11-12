# 蛋白质脂肪族指数

按 Ikai 公式批量计算蛋白质序列的脂肪族指数（Aliphatic Index）。

指数 = 100 × [A + 2.9V + 3.9(I + L)] / N。A、V、I、L 是对应残基的计数，N 是全序列长度。指数用于比较序列组成；热稳定性还需独立证据。

选择一种输入：粘贴单条序列或多条 FASTA、上传 FASTA/TXT/CSV/PDB，或输入 RCSB PDB 编号查询序列。PDB 使用首个模型中有坐标的蛋白链。CSV 接受 `id,sequence` 或 `name,seq`。解析忽略空白和大小写，发现非法残基或空记录时停止本批。

`results.csv` 含编号、长度和两位小数的指数。兼容的 `aliphatic_index.csv` 保留四种残基计数和六位小数。

```bash
python3 run_aliphatic_index.py examples/example.fasta --out-dir output
bash examples/test_run.sh
PYTHONPATH=. python3 examples/test_inputs.py
```

使用 PDB 输入时运行 `python3 -m pip install --no-deps biopython==1.85`，以安装残基映射表。玻尔部署见[发布步骤](bohrium/bohrium-publish.md)，双语正文保存在 [bohrium/docs](bohrium/docs/)。
