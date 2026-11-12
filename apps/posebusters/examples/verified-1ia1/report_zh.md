# PoseBusters 对接姿势质量检查报告

- 检查模式：**redock（预测姿势 + 蛋白 + 晶体配体：另查与参考的一致性和 RMSD）**
- 预测姿势文件：`1ia1_ligand.sdf`
- 蛋白结构：`1ia1_protein_one_lig_removed_ligand_removed.pdb`
- 预处理：已从蛋白结构中移除目标配体 TQ3（19 个原子）
- 晶体参考配体：`1ia1_ligand.sdf`
- 本次执行检查项：**28 项**
- 姿势数：**1**，全部通过（PB-valid）：**1**，存在问题：**0**
- PB-valid 比例：**100.0%**

## 结论

1 个姿势全部通过检查，化学与物理上都站得住，可以进入下一步（如相互作用分析、打分排序、自由能计算）。

## 逐个姿势

| 序号 | 分子 | 构象位置 | 结果 | 通过 / 总数 | 未通过项 |
| --- | --- | --- | --- | --- | --- |
| 1 | TQ3 | 0 | ✅ 通过 | 28 / 28 | — |

## 本次执行的检查项

**A 读取与化学有效性**

- 预测姿势可读取（`mol_pred_loaded`）
- 参考配体可读取（`mol_true_loaded`）
- 蛋白结构可读取（`mol_cond_loaded`）
- 化学净化通过（`sanitization`）
- 可转为 InChI（`inchi_convertible`）
- 原子全部相连（`all_atoms_connected`）
- 无自由基（`no_radicals`）

**B 与参考分子的一致性**

- 分子式与参考一致（`molecular_formula`）
- 成键与参考一致（`molecular_bonds`）
- 双键立体化学与参考一致（`double_bond_stereochemistry`）
- 四面体手性与参考一致（`tetrahedral_chirality`）

**C 分子内几何**

- 键长合理（`bond_lengths`）
- 键角合理（`bond_angles`）
- 分子内无原子碰撞（`internal_steric_clash`）
- 芳环保持共平面（`aromatic_ring_flatness`）
- 非芳环未被压平（`non-aromatic_ring_non-flatness`）
- 双键周围共平面（`double_bond_flatness`）
- 内部能量合理（`internal_energy`）

**D 与口袋的相容性**

- 配体未脱离蛋白（`protein-ligand_maximum_distance`）
- 与蛋白无原子碰撞（`minimum_distance_to_protein`）
- 与有机辅因子无碰撞（`minimum_distance_to_organic_cofactors`）
- 与金属离子无碰撞（`minimum_distance_to_inorganic_cofactors`）
- 与结晶水无碰撞（`minimum_distance_to_waters`）
- 与蛋白体积重叠不超限（`volume_overlap_with_protein`）
- 与有机辅因子体积重叠不超限（`volume_overlap_with_organic_cofactors`）
- 与金属离子体积重叠不超限（`volume_overlap_with_inorganic_cofactors`）
- 与结晶水体积重叠不超限（`volume_overlap_with_waters`）

**E 与晶体结构的吻合度**

- 与晶体姿势 RMSD ≤ 2 Å（`rmsd_≤_2å`）

## 注意事项

- PoseBusters 判断的是姿势**合不合理**，不预测结合强度（Kd / ΔG），也不替代打分函数排序。
- 「与结晶水无碰撞 / 体积重叠」这两项：如果对接时本就应该置换掉该水分子，失败是预期之内的，可结合实际判断。
- RMSD ≤ 2 Å 只在提供了晶体参考配体时有意义；没有参考结构时，通过全部检查只说明姿势合理，不等于姿势正确。
- 本 App 不调用任何第三方 API，不含密钥。

## 引用

- Buttenschoen, M., Morris, G. M., Deane, C. M. PoseBusters: AI-based docking methods fail to generate physically valid poses or generalise to novel sequences. *Chem. Sci.* **15**, 3130-3139 (2024). doi:10.1039/D3SC04185A
- PoseBusters 许可：BSD-3-Clause。