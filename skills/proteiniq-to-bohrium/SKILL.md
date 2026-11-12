---
name: proteiniq-to-bohrium
description: Select a ProteinIQ tool and implement an independently runnable Bohrium offline App. Use when the user wants to turn ProteinIQ tools into Bohrium images and Apps, verify their results, and save the source to the ZhuYanTech/bohrium-apps repository.
---

# 将 ProteinIQ 工具部署到玻尔

1. 用 Ego Lite 查看用户打开的 ProteinIQ、玻尔和 GitHub 标签页。先核对 `ZhuYanTech/bohrium-apps` 的 `apps/` 与玻尔开发者中心，避免重复创建。按用户范围挑选候选。初次验证优先选能独立运行、CPU 足够、有明确方法和可手算基准的工具。需要复用第三方代码或权重时，核对许可与分发条件。
2. 在仓库的 `apps/<slug>/` 实现独立计算入口、`launching.py`、Dockerfile、应用元数据和输入样例。参考已验证的 [脂肪族指数应用](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/aliphatic-index)。保留工具出处和算法引用。先验证正常及无效输入，直接执行 Launching 入口，并用 `--gen-schema` 检查平台参数声明。提交用户授权保存的代码。
3. 构建镜像并验证容器，再通过玻尔发布镜像。核对项目、现有镜像名称和剩余配额。用一个与版本绑定的标签，提交结果未知时先回查同名镜像和状态再决定是否重试。
4. 在开发者中心先为镜像仓库绑定已可用的镜像版本，再创建标准离线任务，给 App 版本绑定同一镜像。等版本从「处理中」变为「待发布」，用该版本操作栏的「查看测试链接」检查表单并运行样例。下载输出，对照预期值。用户只要求创建时，以测试版本交付。公开上架按用户要求处理。

## 构建和上传

可使用[自定义镜像创建页](https://www.bohrium.com/web-images/custom/create)。网页构建只接收 Dockerfile 文本时，将构建所需源文件放在可访问的固定提交地址。网页校验曾返回 HTTP 405；先确认列表里没有同名记录，再切换本地路径。远程命令行构建同样只发送文本，并可能从现金余额计费。

本地构建路径已验证：

```bash
bohr auth status --verify
bohr project list
docker build --platform linux/amd64 -t <app>:<tag> <app-directory>
# 以 docker run 调用容器里的 Launching 入口，用样例核对输出。
bohr image push <app>:<tag> <namespace>/<app>:<tag> --project-id <project-id> -o json
```

官方命令行安装和设备授权见[安装文档](https://docs.bohrium.com/docs/bohrctl/install/)。Apple Silicon 上先确认 Docker 能执行 `linux/amd64` 容器。推送完成以回执里的 `status: 1`、`imageUrl` 和 `digest` 为准。开发者中心选择该 `imageUrl` 对应的镜像，使用容器里已验证的绝对入口和解释器路径。示例应用使用 `/app/launching.py` 和 `/usr/local/bin/python3`。

## 验收与余额不足

分别记录镜像推送、App 版本和任务输出。测试页提示余额不足时，查可用的批处理 CPU 机型，用同项目、同镜像、同 Launching 入口验证实际云端计算。运行前核对当前定价与项目支持的支付方式。

```bash
bohr batchjob machine list --choose-type cpu --sort price -o json
bohr batchjob submit --project-id <project-id> --sku-id <verified-sku-id> \
  --image <imageUrl> --input <sample-directory> --out-file <result-path> \
  --command '<container-entry-command>' --max-run-time 5m --max-wait-time 5m \
  --payment-source balance --yes -o json
bohr batchjob wait <jobId> --timeout 1m -o json
bohr batchjob files <jobId> -o json
bohr batchjob download <jobId> --dest <new-directory> --path <result-path> -o json
```

脂肪族指数在 XLab-Project 验收时，`c1_m2_cpu` 是批处理的 0 元 CPU 机型，现金计费提交成功。XLab-Project 拒绝光子支付。App 测试页当时只提供付费 CPU，余额不足阻止入队。遇到类似情形，在交付时区分已通过的云端批处理结果与仍待运行的 App 表单任务。
