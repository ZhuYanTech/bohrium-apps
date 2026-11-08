# PLIP 蛋白-配体相互作用分析报告

- 输入：本地文件 3MXF.pdb
- PLIP 版本：3.0.1（XML 中记录）
- 模型：1
- 检测到的配体：DMS（A链，残基 171，SMALLMOLECULE）, EDO（A链，残基 170，SMALLMOLECULE）, EDO（A链，残基 2，SMALLMOLECULE）, EDO（A链，残基 3，SMALLMOLECULE）, JQ1（A链，残基 1，SMALLMOLECULE）
- 相互作用总数：27
- 按配体分开：JQ1 14 个; EDO 8 个; DMS 5 个

## 按类型统计

| 相互作用类型 | 数量 |
| --- | ---: |
| 疏水相互作用 | 11 |
| 氢键 | 9 |
| 水桥 | 5 |
| 盐桥 | 2 |

## 按配体统计（不要只看总数）

| 配体 | 数量 | 备注 |
| --- | ---: | --- |
| JQ1 | 14 | 目标配体 |
| EDO | 8 | 常见结晶溶剂/添加剂，不是目标配体 |
| DMS | 5 | 常见结晶溶剂/添加剂，不是目标配体 |

注意：总数 27 个里有 13 个来自结晶溶剂，评价结合模式时请看目标配体那一行；只想看目标配体时可用 `--ligand <配体名>` 或 `--exclude-solvents` 重新跑。

## 关键残基（按相互作用次数排序）

| 残基 | 相互作用数 |
| --- | ---: |
| ASP145（A链） | 4 |
| ILE146（A链） | 3 |
| THR103（A链） | 2 |
| ASN140（A链） | 2 |
| TRP81（A链） | 2 |
| LEU94（A链） | 2 |
| TYR97（A链） | 2 |
| ASP144（A链） | 1 |
| ILE100（A链） | 1 |
| LYS102（A链） | 1 |

解读提示：排在前面的残基通常是结合的关键锚点；例如 ASP145（A链） 参与了 4 个相互作用，突变或修饰它时要格外小心。

## 输出文件

- `interactions.csv`：每行一个相互作用，可直接用 Excel / pandas 打开。
- `plip_raw/`：PLIP 原始 XML / TXT 报告。
- `images/`：如有 PNG 图片会在此（默认不生成，见 README 说明）。

## 注意事项

- PLIP 只检测“有什么相互作用”，不预测结合亲和力（Kd / ΔG），不要把相互作用个数直接当成亲和力高低。
- 距离、角度阈值用的是 PLIP 默认值；如需调整，请在玻尔 App 的高级参数里说明。

## 引用

- Salentin, S. et al. PLIP: fully automated protein-ligand interaction profiler. Nucleic Acids Res. 43 (W1), W443–W447 (2015). doi:10.1093/nar/gkv315
- Schake, P., Bolz, S. N. et al. PLIP 2025: introducing protein–protein interactions to the protein–ligand interaction profiler. Nucleic Acids Res. (2025), gkaf361. doi:10.1093/nar/gkaf361
- PLIP 许可：GNU GPLv2；代码与 Docker 镜像：github.com/pharmai/plip，Docker Hub：pharmai/plip。
