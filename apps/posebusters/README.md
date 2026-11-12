# PoseBusters 对接姿势质量检查 — 玻尔（Bohrium）App

> 本 App 是 [`bohrium-apps`](https://github.com/ZhuYanTech/bohrium-apps) 单一仓库中的应用，位于 `apps/posebusters/`。
> 以下命令均在 `apps/posebusters/` 目录内执行。

对接或 AI 结构预测出来的配体姿势，到底站不站得住？
这个 App 逐项检查化学有效性、分子内几何、与口袋的相容性、与晶体结构的吻合度，
输出明细表、每个姿势一行的汇总表，和一份中文解读报告。

## 为什么需要它

打分函数只告诉你"这个姿势得几分"，不告诉你"这个姿势物理上成不成立"。
AI 对接方法尤其容易产出打分很高、但键长畸变、环被压平、或者直接和蛋白穿模的姿势。
PoseBusters 原论文的结论就是：多数 AI 对接方法生成的姿势过不了物理有效性检查。
把这一步放在打分排序之前，能省掉后面一连串白跑的计算。

## 检查范围（按输入自动判定）

| 模式 | 输入 | 检查项数 | 查什么 |
| --- | --- | --- | --- |
| `mol` | 只给姿势 | 12 | 化学有效性 + 分子内几何 |
| 仅参考 | 姿势 + 晶体配体 | 18 | 检查化学、几何及与参考的一致性，跳过口袋相容性 |
| `dock` | 姿势 + 蛋白 | 22 | 再加与口袋的相容性（碰撞、穿模、是否跑出口袋） |
| `redock` | 姿势 + 蛋白 + 晶体配体 | 28 | 再加与参考的一致性和 RMSD ≤ 2 Å |

检查项分五组：A 读取与化学有效性、B 与参考分子的一致性、C 分子内几何、
D 与口袋的相容性、E 与晶体结构的吻合度。报告里每一项都有中文名、
所属分组，以及失败时的原因解读和处理建议。

## 输入 / 输出

| | 内容 |
| --- | --- |
| 输入 | **待检查的配体姿势**（SDF/MOL/MOL2/PDB，必填，可含多个分子或构象）；**受体**（PDB/SDF/MOL/MOL2，可选）或 **PDB 编号**（4 位，自动从 RCSB 下载）；**晶体参考配体**（SDF/MOL/MOL2/PDB，可选）；**从蛋白中删除的配体残基名**（PDB 可选，玻尔表单默认保留原受体） |
| 输出 | `summary.csv`（每个姿势一行：是否 PB-valid、通过/未通过项数、未通过项中文名）、`results.csv`（每项检查一列的明细）、`report_zh.md`（中文报告）、`posebusters_raw/`（原始 CSV + 下载/剥离后的蛋白结构） |

## 批量配对与高级设置

玻尔表单支持预测、参考和受体三组文件的 ZIP 输入。按每组在 ZIP 中的条目顺序进行 1-based 编号。将配对表放在根目录 `pairs.csv`，或粘贴到配对字段。表头为 `mol_pred,mol_true,mol_cond`，后两列可选。批量结果包含逐配对目录及根目录汇总。详见[中英文帮助](bohrium/docs/)。

可切换自动、预设、快速或自定义配置，指定每个输入的前 N 个姿势和原生报告格式。详细输出增加诊断列。汇总把通过、失败及未评估分开，任一预期检查为空时，该项不计入通过数。

## 受体保留了待检查的配体

如果蛋白结构里还留着你要对接的那个配体，预测姿势就会和**它自己**碰撞，
结果是所有口袋相容性检查全部失败——看起来像姿势很差，其实是输入没准备好。

玻尔表单默认保留输入受体，可显式填写待移除残基名或启用自动推断。旧版命令行保持原默认，使用 `--no-auto-strip` 保留受体原样。移除只适用于 PDB，并按残基名操作。

## 本地运行（不用玻尔账号也能试）

```bash
# 1. 装依赖
pip install posebusters==0.6.5 rdkit==2026.9.2

# 2. 用 PoseBusters 自带的基准结构跑一个 redock 例子
DS=$(python3 -c "import posebusters,os;print(os.path.join(os.path.dirname(posebusters.__file__),'datasets','pdb'))")
python3 run_posebusters.py \
  --mol-pred  $DS/1ia1/1ia1_ligand.sdf \
  --mol-true  $DS/1ia1/1ia1_ligand.sdf \
  --protein   $DS/1ia1/1ia1_protein_one_lig_removed.pdb \
  --out-dir   ./pb-output

# 3. 看结果
cat pb-output/report_zh.md
cat pb-output/summary.csv
```

晶体配体对自己做 redock，应当 **28 项全过（PB-valid 100%）**。

```bash
# 蛋白用 PDB 编号自动下载（会自动剥离目标配体 TQ3）
python3 run_posebusters.py --mol-pred $DS/1ia1/1ia1_ligand.sdf \
  --mol-true $DS/1ia1/1ia1_ligand.sdf --pdb-id 1IA1 --out-dir ./pb-output-pdbid

# 只查分子本身，不给蛋白（mol 模式，12 项）
python3 run_posebusters.py --mol-pred ./my_docked_poses.sdf --out-dir ./pb-output-mol
```

```bash
# 一键验证（正例 4 个 + 反例 2 个 + 三种模式 + 错误处理）
bash examples/test_run.sh
```

## 怎么读结果

- `summary.csv` 的 `PB_valid` 列是"是"的姿势，才建议进入后续分析
  （相互作用分析、打分排序、自由能计算）。
- 如果失败集中在 **C 分子内几何**，多半是生成模型的构象质量问题——
  换采样方式或做一次力场优化。
- 如果失败集中在 **D 与口袋的相容性**，多半是对接位置或搜索框设错了——
  回去检查口袋定义。
- **E 的 RMSD ≤ 2 Å** 只在有晶体参考时才有意义。没有参考结构时，
  通过全部检查只说明姿势**合理**，不等于姿势**正确**。

## 和仓库里其他 App 的衔接

`boltz2` / `openfold3` 产生复合物结构 → **本 App 把关姿势质量** →
`plip` 分析通过筛选的姿势的相互作用。中间这一步能挡掉大量无效后续计算。

## 发布到玻尔

见 [`bohrium/bohrium-publish.md`](bohrium/bohrium-publish.md)。
使用 [Dockerfile](Dockerfile) 本地构建并通过玻尔命令行推送。开发者中心的双语介绍与帮助正文保存在 [`bohrium/docs/`](bohrium/docs/)。

## 许可与引用

- PoseBusters 本身：**MIT**。
- 本 App 的封装代码与文档：随仓库以 MIT 发布。
- [PoseBusters 上游开源仓库](https://github.com/maabuu/posebusters)
- [玻尔封装开源仓库](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)

按 PDB 编号查询时需要访问 RCSB。
