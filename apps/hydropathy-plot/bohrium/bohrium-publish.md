# 蛋白质亲疏水性曲线 · 1.0.0

在此应用目录执行构建和容器验收。

```bash
docker build --platform linux/amd64 -t hydropathy-plot:1.0.0 .
docker run --rm --platform linux/amd64 hydropathy-plot:1.0.0 bash examples/test_run.sh
```

首次部署时将此应用的镜像推送至自己的仓库。实际发布记录见[批量验收清单](../../BATCH-10-VERIFICATION.md)。

```bash
bohr image push hydropathy-plot:1.0.0 zhuyan-xlab/hydropathy-plot:1.0.0 --project-id <project-id> -o json
```

- 开发者镜像版本绑定 `zhuyan-xlab/hydropathy-plot:1.0.0`，架构 `linux/amd64`。
- App 类型为标准离线任务，使用该专属镜像，入口为 `/app/launching.py`，解释器为 `/usr/local/bin/python3`。
- [字段声明](schema.json)来自镜像的 Launching 入口。主结果是 `hydropathy.csv`。保存 [中英文介绍及帮助](docs/)后检查版本测试页。
- [镜像版本](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/hydropathy-plot?tab=versions) · [App 版本](https://www.bohrium.com/developer/detail/hydropathy-plot?tab=versions) · [版本测试页](https://www.bohrium.com/apps/hydropathy-plot/job?type=app&deploymentId=502429&mode=debug)
