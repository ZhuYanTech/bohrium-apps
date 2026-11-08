# PLIP 结合模式解析 — 使用指南

## 这个 App 是做什么的

上传蛋白-配体复合物 PDB 文件，或输入一个 PDB 编号，分析其中的非共价相互作用：
氢键、疏水、卤键、盐桥、π-堆积、水桥等。输出相互作用清单（CSV）和中文解读报告，
帮你看懂分子为什么能结合、关键残基是哪些。

底层为开源 PLIP 3.0.1，CPU 即可运行，单结构通常 5 分钟内完成。

## 使用步骤

1. 上传 PDB 文件（须含 HETATM 配体记录），或输入 4 位 PDB 编号（如 1VSN、3MXF，
   会自动从 RCSB 下载）。二选一；同时给了优先用上传文件。
2. （可选）模型编号：多模型 PDB（如 NMR 结构）选第几个模型，默认 1。
3. （可选）只分析指定配体：填配体三字母代码，如 JQ1；留空分析全部配体。
4. （可选）过滤结晶溶剂：勾选后过滤 DMS、EDO 等常见结晶溶剂/添加剂，只保留目标配体。
5. 提交任务，下载结果。

## 输出文件

- `interactions.csv`：每行一个相互作用——类型（中英）、配体、残基（链 + 编号）、
  距离、详细参数。
- `report_zh.md`：中文解读报告——按类型计数、关键残基 Top 10、按配体统计、注意事项。
- `plip_raw/`：PLIP 原始 XML / TXT 报告，供复核。

## 示例

- 1VSN（Cathepsin K + 抑制剂 NFT）：13 个相互作用——氢键 7、疏水 4、卤键 2；
  关键残基 ASP61、TYR67。
- 3MXF（BRD4 + JQ1）：JQ1 本身 14 个（疏水 11、水桥 2、氢键 1，含 ASN140
  经典氢键）；其余 13 个是结晶溶剂 DMS、EDO 的，报告会按配体分开计数。

## 如何解读结果

- 相互作用个数不是亲和力：个数多 ≠ 结合强。只用于看结合模式、找关键残基、
  对照构效关系。
- 溶剂：结晶溶剂也会被算进去。报告按配体分开计数并标出溶剂占比；只看目标配体时
  用「只分析指定配体」或勾选「过滤结晶溶剂」。
- 判定阈值用 PLIP 默认距离/角度，详见 PLIP 文档。

## 常见问题

- 任务失败 / 无报告：多半是 PDB 里没有配体（HETATM），或文件损坏。
- 0 个相互作用：结构里可能没有配体，或配体离蛋白太远；检查 HETATM 记录和
  配体三字母代码。
- 个数和文献对不上：先看是不是溶剂被算进去了；再看模型编号（多模型 PDB 默认
  只取模型 1）和 PLIP 版本。
- 没有 PNG 图片：正常。图片生成功能需要 PyMOL，本 App 未提供；3D 查看请用
  PyMOL 或 Mol* 打开原 PDB。
- PLIP 只检测相互作用，不预测结合亲和力（Kd / ΔG）。

## 引用

- Salentin, S. et al. PLIP: fully automated protein-ligand interaction profiler.
  Nucleic Acids Res. 43 (W1), W443–W447 (2015). doi:10.1093/nar/gkv315
- Schake, P., Bolz, S. N. et al. PLIP 2025: introducing protein–protein interactions
  to the protein–ligand interaction profiler. Nucleic Acids Res. (2025), gkaf361.
  doi:10.1093/nar/gkaf361
