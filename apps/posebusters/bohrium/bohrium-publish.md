# PoseBusters 玻尔部署

开发者镜像仓库为 `zhuyan-xlab/posebusters`，App 标识为 `posebusters-pose-validator`。标准离线任务使用 CPU。应用元数据见 [app.json](app.json)，镜像与 App 的双语介绍及帮助见 [docs/](docs/)。

## 构建与推送

先检查项目自定义镜像和开发者镜像版本。需要构建时，在 `apps/posebusters/` 下执行：

```bash
bohr auth status --verify
bohr project list
docker build --platform linux/amd64 -t posebusters:1.0.0 .
docker run --rm --platform linux/amd64 posebusters:1.0.0 bash /app/examples/test_run.sh
bohr image push posebusters:1.0.0 zhuyan-xlab/posebusters:1.0.0 \
  --project-id 4812217 -o json
```

项目 ID 示例对应 XLab-Project。构建过程直接运行 Launching 入口，检查内置 1IA1 基准的 28 项是否全部通过。推送成功时，记录回执的 `id`、`imageUrl`、`status: 1` 和 `digest`。

## 绑定到开发者中心

1. 在[镜像仓库](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/posebusters?tab=versions)的「版本管理」绑定推送回执对应的镜像，标签 `1.0.0`，架构 `linux/amd64`。
2. 在[开发者中心](https://www.bohrium.com/developer)创建或打开同名标准离线 App。App 版本选择同一镜像，入口 `/app/launching.py`，Python `/usr/local/bin/python3`，推荐 CPU 机型。
3. 补全镜像和 App 的双语描述、标签、介绍与帮助。刷新后分别检查中英文页和 GitHub 来源链接。
4. App 版本进入「待发布」后，打开「查看测试链接」，检查姿势、受体、参考配体等输入。上传同一晶体配体作为待检查姿势及参考，并上传对应受体文件。核对 `summary.csv`、`results.csv` 和 `report_zh.md`。

## 在镜像内复现样例

以下命令可以作为批处理的任务命令，样例来自容器内置的 PoseBusters 公开测试集：

```bash
set -e
ds="$(python -c 'import pathlib, posebusters; print(pathlib.Path(posebusters.__file__).parent / "datasets/pdb/1ia1")')"
python /app/launching.py --mol_pred "$ds/1ia1_ligand.sdf" \
  --protein_file "$ds/1ia1_protein_one_lig_removed.pdb" \
  --mol_true "$ds/1ia1_ligand.sdf" --output_dir ./output
```

预期 `summary.csv` 仅有一个姿势，28 项全部通过，`PB_valid` 为「是」。测试页提交受余额限制时，可使用相同项目和镜像在批处理的免费 CPU 机型验算，确认当前报价和计费方式后再提交。
