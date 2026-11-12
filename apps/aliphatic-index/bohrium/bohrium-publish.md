# 玻尔部署

兼容性更新版使用独立镜像和 App 版本 `1.1.0`。下方 `1.0.0` 记录供复现旧版。

部署目标为 XLab-Project 下的 Linux x86-64 容器和标准离线任务。应用标识为 `protein-aliphatic-index`，元数据见 [app.json](app.json)。

## 本地构建并推送

按[玻尔官方文档](https://docs.bohrium.com/docs/bohrctl/install/)安装并登录命令行，确认当前账号能访问目标项目。以下命令从本目录的上一级 `apps/aliphatic-index` 执行，示例使用 XLab-Project 的项目 ID。

```bash
bohr auth status --verify
bohr project list
docker build --platform linux/amd64 -t protein-aliphatic-index:1.0.0 .
docker run --rm --platform linux/amd64 protein-aliphatic-index:1.0.0 \
  python /app/launching.py --fasta /app/examples/example.fasta --output_dir /tmp/smoke
bohr image push protein-aliphatic-index:1.0.0 \
  zhuyan-xlab/protein-aliphatic-index:1.0.0 --project-id 4812217 -o json
```

推送成功时，回执应包含 `status: 1`、`imageUrl` 和 `digest`。保存返回的地址，用于开发者中心选择对应镜像。在 Apple Silicon 上要确认 Docker 支持运行 `linux/amd64` 容器。

## 通过镜像中心构建

先将源码推送到公开 GitHub 仓库，然后运行 `python3 bohrium/imagehub_dockerfile.py <完整提交号>`。将生成内容粘贴到[自定义镜像创建页](https://www.bohrium.com/web-images/custom/create)，选择「基于 Dockerfile」。该页面的 Dockerfile 校验曾返回 HTTP 405。遇到同类错误时，先检查项目镜像列表有无同名记录，再使用上面的本地推送流程。

## 配置应用版本

1. 在[开发者镜像仓库](https://www.bohrium.com/developer/image-hub)创建或打开同名仓库，选择「版本管理 → 新建版本 → 选择 Bohrium 镜像」，绑定已推送的 `1.0.0`。系统架构选择 `linux/amd64`。
2. 在[开发者中心](https://www.bohrium.com/developer)创建标准离线任务，进入「版本管理 → 新建版本」。选择同一个玻尔镜像，入口为 `/app/launching.py`，解释器为 `/usr/local/bin/python3`，推荐机型为 `c2_m2_cpu`。
3. 以 [example.fasta](../examples/example.fasta) 验证应用，CSV 应包含 `alanine=100`、`leucine=390`、`mixed=292.5`、`no-aliphatic=0`。用版本的实际运行结果核对输出文件及数值。

## 本次验证记录

- 镜像记录 `193577`，标签 `1.0.0`，推送回执状态 `1`，摘要 `sha256:56ff6f9779fe015d7667f18f1a31c11a4d71e391b220b1c865e3fa8ac9762197`。
- App 版本 `1.0.0` 状态「待发布」。测试页已显示 FASTA 上传项，提交时平台返回「账户余额不足，请充值」。
- 同项目使用批处理的 0 元机型 `c1_m2_cpu`（提交时的 SKU 为 `18903`）运行同一镜像和入口，任务 `3254880fe4344f47ac6890a8f3593362` 成功。下载的 `output/aliphatic_index.csv` 与本地结果逐字节一致。
