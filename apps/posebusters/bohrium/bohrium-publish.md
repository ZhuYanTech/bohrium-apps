# PoseBusters 发布步骤

App ID `posebusters-pose-validator`，类型：标准离线任务（Standard Offline Task）。
纯 CPU，不需要 GPU。发布分三步：建镜像 → 测运行 → 建 App。

> 原则：玻尔有自己的计算引擎。我们只创建/发布应用，用户在玻尔上自己开
> 计算节点、用玻尔算力跑，算力费由用户付给玻尔。本仓库不调用任何第三方
> API，不含任何密钥。

## 0. 前置

封装脚本是在镜像构建时从公开仓库 `git clone` 下来的，
**所以 `apps/posebusters/` 必须先推到 GitHub main 分支，再去建镜像**。
否则构建会拉到旧代码或直接失败。

## 1. 建镜像（镜像中心）

打开镜像中心 https://www.bohrium.com/developer/image-hub，
新建镜像，名称 `zhuyan-xlab/posebusters`，标签 `1.0`，
把 `bohrium/Dockerfile.imagehub` 的全文粘贴进 Dockerfile 输入框，提交构建。

镜像约 1.5 GB（主要是 RDKit），构建通常几分钟。
构建日志里应当看到：

```
posebusters 0.6.5
rdkit 2026.9.2
run_posebusters.py OK
... PB-valid 100.0%
构建期自检通过：1IA1 晶体配体 28 项全过
```

最后两行是 Dockerfile 里内置的自检：用 PoseBusters 自带的 1IA1 跑一次 redock，
必须 28 项全过，否则构建直接失败。**看到这行才算镜像可用。**

镜像中心的构建无需本地 Docker；若要本地复现：

```bash
cd apps/posebusters
docker build -t zhuyan-xlab/posebusters:1.0 -f bohrium/Dockerfile.imagehub .
```

## 2. 测运行（玻尔节点，CPU）

用镜像在玻尔节点上跑一次，输入用 PoseBusters 自带的 1IA1
（镜像里就有，路径见下），确认 `summary.csv`、`results.csv`、
`report_zh.md` 都生成，且 PB-valid 100%：

```bash
DS=$(python3 -c "import posebusters,os;print(os.path.join(os.path.dirname(posebusters.__file__),'datasets','pdb'))")
python3 /app/run_posebusters.py \
  --mol-pred $DS/1ia1/1ia1_ligand.sdf \
  --mol-true $DS/1ia1/1ia1_ligand.sdf \
  --protein  $DS/1ia1/1ia1_protein_one_lig_removed.pdb \
  --out-dir  ./output
```

要跑完整验证（正例 + 反例 + 三种模式 + 错误处理）：

```bash
bash /app/examples/test_run.sh      # 退出码 0 表示全部符合预期
```

## 3. 建 App（开发者中心）

打开 https://www.bohrium.com/developer ，创建 App，
元数据见本目录的 `app.json`：

- App ID：`posebusters-pose-validator`
- App 名称：`PoseBusters 对接姿势质量检查`
- 类型：标准离线任务
- 中英文描述：见 `app.json` 的 `description_zh` / `description_en`
- 新建版本：镜像选上一步的 `zhuyan-xlab/posebusters:1.0`，
  **EntryPoint 填 `/app/launching.py`**，机型选 CPU（2 核 4 G 足够）
- 审核要点（玻尔开发者中心协议）：App 须为自行开发或有管理权限的内容，
  不得侵犯第三方知识产权。PoseBusters 为 BSD-3-Clause，
  App 页面须保留其引用和许可说明（`app.json` 里已写好，发布时不要删）。

## 4. 上架后验收

- [ ] App 详情页能打开，输入项与 `app.json` 一致（6 项输入，1 必填 5 可选）
- [ ] 只传一个 SDF（mol 模式）→ 12 项检查，能出报告
- [ ] 传 SDF + 蛋白（dock 模式）→ 22 项
- [ ] 传 SDF + 蛋白 + 晶体配体（redock 模式）→ 28 项
- [ ] 用 PDB 编号 `1IA1` 跑一次，确认日志里有"已从蛋白结构里删掉 TQ3"
      且结果 PB-valid 100%（这条最能暴露配体剥离有没有生效）
- [ ] 下载 `report_zh.md`，确认中文报告可读、结论先行

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| 所有口袋相容性检查都失败 | 多半是蛋白里还留着要对接的那个配体。用 `--strip-ligand <残基名>` 指定，或确认自动推断生效 |
| 失败项是"与有机辅因子碰撞" | 同上——留在 PDB 里的目标配体会被当成有机辅因子 |
| RMSD 一项显示未执行 | 没给晶体参考配体。只有 redock 模式才有这一项 |
| 与结晶水碰撞 | 若对接时本就该置换该水分子，属预期之内，可结合实际判断 |
| 构建日志没有"构建期自检通过" | 镜像不可用，别上架。多半是仓库代码没推上去，或依赖版本有变 |
| 镜像推送报项目配额不足 | 先确认项目里没有卡在 Building 状态的镜像记录 |

## 不做的事

- 不把任何 API Key、账号密码放进镜像、代码或 `app.json`。
- 不在玻尔 App 里调用任何第三方 API。
