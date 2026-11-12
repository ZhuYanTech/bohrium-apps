# 验证记录 — PoseBusters 玻尔 App

验证日期：2026-11-12
环境：Ubuntu 24.04，Python 3.13，posebusters 0.6.5，rdkit 2026.9.2
一键复跑：`bash examples/test_run.sh`（退出码 0 表示全部符合预期）

## 结论

正例、反例、剥离逻辑、三种模式、错误处理五组验证全部符合预期。
反例的失败项精准落在各自对应的检查分组上，互不交叉，
说明检查项不是"一出错就全红"，而是确实分别在起作用。

## 1. 正例：晶体配体对自己做 redock，应当全过

PoseBusters 自带的 4 个基准结构，用晶体配体作为"预测姿势"、
同一个配体作为"晶体参考"、去掉该配体的蛋白作为受体。
真实的晶体姿势理应通过全部检查。

| 结构 | 配体 | 检查项数 | 结果 |
| --- | --- | --- | --- |
| 1IA1 | TQ3 | 28 | ✅ 28 / 28，PB-valid 100% |
| 1OF6 | — | 28 | ✅ 28 / 28，PB-valid 100% |
| 1S3V | — | 28 | ✅ 28 / 28，PB-valid 100% |
| 1UOU | — | 28 | ✅ 28 / 28，PB-valid 100% |

产物见 `examples/verified-1ia1/summary.csv` 与 `report_zh.md`。

## 2. 反例：人造缺陷姿势，应当被抓出来且抓对类别

由 1IA1 的晶体配体用 `examples/make_bad_poses.py` 造出两个一定不合格的姿势。

| 反例 | 怎么造的 | 预期失败分组 | 实际未通过项 |
| --- | --- | --- | --- |
| `bad_translated.sdf` | 整体平移 10 Å，离开口袋 | D 与口袋的相容性 + E 吻合度 | `minimum_distance_to_protein`；`volume_overlap_with_protein`；`rmsd_≤_2å` ✅ |
| `bad_squashed.sdf` | 坐标整体缩到 0.5 倍 | C 分子内几何 | `bond_lengths`；`bond_angles`；`internal_steric_clash`；`internal_energy` ✅ |

两组失败项完全落在各自预期的分组内，没有交叉污染：
平移的分子内部几何没动，分子内几何那组全过；
缩放的分子仍在口袋中心附近，RMSD 一项未触发。

产物见 `examples/verified-1ia1/summary_bad_translated.csv`、`summary_bad_squashed.csv`。

## 3. 配体剥离逻辑：与官方预处理文件等价

用 `--pdb-id 1IA1` 从 RCSB 下载的是**完整结构**，里面还留着目标配体 TQ3。
不处理的话，预测姿势会和它自己碰撞。

| 做法 | 结果 |
| --- | --- |
| 直接用下载的完整 1IA1.pdb（`--no-auto-strip`） | ❌ PB-valid 0%：`minimum_distance_to_organic_cofactors`、`volume_overlap_with_organic_cofactors` 两项失败 |
| 自动推断并剥离 TQ3（默认行为） | ✅ 28 / 28，PB-valid 100% |
| 用官方预处理文件 `1ia1_protein_one_lig_removed.pdb` | ✅ 28 / 28，PB-valid 100% |

失败项值得一提：留在 PDB 里的 TQ3 被 PoseBusters 当成了"有机辅因子"，
于是"配体与自己碰撞"表现为**与有机辅因子碰撞**。如果不知道这个坑，
很容易误判成"这个口袋里有辅因子挡路"。

自动剥离从姿势文件的分子名推断出 `TQ3`，删掉 38 个原子，
**保留水（236）、NDP（96）、PO4（10）**——这些是 PoseBusters 做
辅因子和水碰撞检查要用的，不能一起删。
剥离后的结果与官方预处理文件完全一致，剥离逻辑由此得到交叉验证。

## 4. 三种模式：检查项数应递增

| 模式 | 输入 | 检查项数 |
| --- | --- | --- |
| mol | 只给姿势 | 12 |
| dock | 姿势 + 蛋白 | 22 |
| redock | 姿势 + 蛋白 + 晶体配体 | 28 |

12 < 22 < 28 ✅。多给一类输入就多开一组检查，与设计一致。

## 5. 多姿势文件

把 1 个合格姿势和 1 个缺陷姿势放进同一个 SDF，
报告逐个列出：第 1 个 ✅ 28/28，第 2 个 ❌ 24/28（4 项分子内几何未通过），
汇总为 PB-valid 50%。逐姿势判定正常。

> 注：手工用 `cat` 合并 SDF 时要注意，有些 SDF 末尾缺 `$$$$` 分隔符，
> 直接拼接会让相邻两个分子粘连而少读一个。用 RDKit 的 `SDWriter` 合并更稳妥。

## 6. 错误处理

| 情形 | 行为 |
| --- | --- |
| 姿势文件不存在 | ✅ 中文提示「找不到预测姿势文件：…」，退出码 1 |
| PDB 编号非法（如 `ZZZZ`） | ✅ 中文提示「PDB 编号格式不对…」，退出码 1 |
| 给了参考配体但没给蛋白 | ✅ 提示口袋相容性那组检查会跳过，任务继续 |
| 蛋白里有多个有机 HETATM 且未指定剥离目标 | ✅ 列出候选残基名并提示用 `--strip-ligand`，任务继续 |

## 未在本地验证的部分

- 镜像构建：由玻尔镜像中心在线完成。Dockerfile 里带了构建期自检
  （1IA1 必须跑出 PB-valid 100%），构建日志里能直接看到。
- `launching.py` 的表单渲染：依赖 `dp-launching-app`（alpha 版），
  需在玻尔建版本时才能看到实际界面。入口逻辑本身与 `run_posebusters.py`
  共用同一套参数，CLI 路径已完整验证。
