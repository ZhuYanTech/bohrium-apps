## PoseBusters 对接姿势质量检查

PoseBusters 检查对接或结构预测产生的配体姿势是否满足化学和几何条件。它可识别异常键长、分子内碰撞、配体与受体重叠等问题。提供晶体参考时，还可检查分子身份、立体化学以及参考姿势的均方根偏差（RMSD）。

| 模式 | 输入 | 检查项 |
| --- | --- | ---: |
| 分子（mol） | 待检查姿势 | 12 |
| 对接（dock） | 姿势与受体 | 22 |
| 重对接（redock） | 姿势、受体与晶体参考 | 28 |

玻尔版根据输入自动选择模式。通过全部检查表示姿势满足当前模式的条件。结合强度、活性和真实结合构象仍需独立验证。

## 开源仓库

- [PoseBusters 上游实现（BSD-3-Clause）](https://github.com/maabuu/posebusters)
- [ZhuYanTech 玻尔封装（MIT）](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)
