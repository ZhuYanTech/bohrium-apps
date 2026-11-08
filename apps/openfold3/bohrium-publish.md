# OpenFold3 发布步骤

App ID `openfold3`，类型：标准离线任务（Standard Offline Task）。
发布分三步：建镜像 → 测运行 → 建 App。

## 1. 建镜像（镜像中心）

打开镜像中心 https://www.bohrium.com/developer/image-hub，
新建镜像，名称 `zhuyan/openfold3-bohrium-app`，标签 `1.0`，
把 `bohrium/Dockerfile.imagehub` 的全文粘贴进 Dockerfile 输入框，
提交构建。构建耗时较长（约 2.29 GB 检查点 + PyTorch + OpenFold3），
构建日志里确认：检查点文件存在、OpenFold3 与 torch 版本正确、
`run_openfold3.py --help` 通过。

镜像中心的构建无需本地 Docker；本地验证可用：

```bash
docker build -t zhuyan/openfold3-bohrium-app:1.0 .
```

## 2. 测运行（玻尔节点，GPU）

用镜像在玻尔节点上跑一次示例：泛素 1UBQ（76 个残基，
`examples/ubiquitin-1ubq/sequence.fasta`），默认设置（1 种子、5 样本）。
确认 `summary.csv`、`predicted.cif`、`report_zh.md` 均已生成。
若节点无法访问 ColabFold 服务器，改用“关闭生成 MSA”或上传自备 `.a3m` 重跑。

## 3. 建 App（开发者中心）

打开开发者中心，创建 App，填入 `bohrium/app.json` 里的元数据：

- App ID：`openfold3`
- App 名称：`OpenFold3 结构预测`
- 类型：标准离线任务
- 中英文描述：见 `app.json` 的 `description_zh` / `description_en`
- 新建版本：镜像选上一步建好的 `zhuyan/openfold3-bohrium-app:1.0`，
  EntryPoint 填 `/app/launching.py`，机型选 GPU（24 GB 显存起步，32 GB 推荐）

## 发布后检查

- App 详情页可正常打开，输入项与 `app.json` 一致
- 用 1UBQ 示例在 App 里跑一次，确认结果文件完整
- 常见问题：镜像推送报项目配额不足时，先确认项目里没有卡在 Building 状态的镜像记录
