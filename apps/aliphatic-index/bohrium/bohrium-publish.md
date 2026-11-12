# 玻尔部署

1. 推送应用代码到公开 GitHub 仓库并记录完整提交号。
2. 用 `python3 apps/aliphatic-index/bohrium/imagehub_dockerfile.py <完整提交号>` 生成适用于玻尔网页构建的 Dockerfile。它从指定提交获取文件。
3. 在玻尔镜像中心用 XLab-Project 创建 `protein-aliphatic-index:1.0.0`，选择「基于 Dockerfile」，粘贴生成内容并构建。
4. 镜像可用后，在开发者中心创建标准离线任务 `protein-aliphatic-index`。镜像地址填平台生成的完整地址，入口使用 `/app/launching.py`，运行资源选 CPU。名称、输入和输出见 `app.json`。
5. 使用 `examples/example.fasta` 试运行，核对输出的四个指数为 100、390、292.5 和 0。
