---
name: proteiniq-to-bohrium
description: Create or finish an independently runnable Bohrium offline App based on a ProteinIQ tool or an existing open-source wrapper. Use for picking tools, recovering unfinished mirror and App records, completing bilingual listing content, verifying outputs, and saving the implementation to ZhuYanTech/bohrium-apps.
---

# 将 ProteinIQ 工具部署到玻尔

1. 用 Ego Lite 查看用户打开的 ProteinIQ、玻尔和 GitHub 标签页。先核对 `ZhuYanTech/bohrium-apps` 的 `apps/` 与玻尔开发者中心，避免重复创建。按用户范围挑选候选。初次验证优先选能独立运行、CPU 足够、有明确方法和可手算基准的工具。需要复用第三方代码或权重时，核对许可与分发条件。
2. 在仓库的 `apps/<slug>/` 实现独立计算入口、`launching.py`、Dockerfile、应用元数据和输入样例。参考已验证的 [脂肪族指数应用](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/aliphatic-index)。在代码中保留上游许可证和必要引用。先验证正常及无效输入，直接执行 Launching 入口，并用 `--gen-schema` 检查平台参数声明。逐一核对所宣称的文件格式与实际解析能力。若详细输出开关只增加诊断列，用同一输入比较开关前后的汇总结论。提交用户授权保存的代码。
3. 分别检查项目自定义镜像、开发者镜像仓库的版本和开发者 App 的版本。空镜像仓库只表示名称已创建。项目已有可用镜像时，核对架构、版本、入口和样例后复用，已有仓库或 App 则在原记录续做。需要新镜像时，先本地验证容器再推送。用一个与版本绑定的标签，提交结果未知时先回查同名镜像和状态再决定是否重试。
4. 在开发者中心先为镜像仓库绑定已可用的镜像版本，再创建标准离线任务，给 App 版本绑定同一镜像。等版本从「处理中」变为「待发布」，用该版本操作栏的「查看测试链接」检查表单并运行样例。下载输出，对照预期值。用户只要求创建时，以测试版本交付。公开上架按用户要求处理。

## 补全开发者页面

镜像和 App 分别填写中英文简述、相关标签、中文和英文介绍、中文和英文帮助。介绍交代算法目的、输入决定的模式和解释边界；帮助写实际文件格式、配置和结果文件，并给一个可复现的样例。以来源页校对算法和示例，以部署版本为准核对输入与输出。来源页额外支持的操作只在确有必要时说明差异。按用户要求，玻尔页面的「来源」只链接开源 GitHub 仓库，保留适用的上游许可证和归属。

用 Ego Lite 编辑时分别保存每个语言页。切换栏目后等当前编辑器或文档加载完成，遇到白屏先回到相同栏目并检查上次保存的内容。最后刷新，逐页核对描述、标签、八份文档、示例数值和来源链接。可以把双语正文保存在应用的 `bohrium/docs/`，参考 [PoseBusters 文档](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters/bohrium/docs)。

## 构建和上传

可使用[自定义镜像创建页](https://www.bohrium.com/web-images/custom/create)。网页构建只接收 Dockerfile 文本时，将构建所需源文件放在可访问的固定提交地址。网页校验曾返回 HTTP 405；先确认列表里没有同名记录，再切换本地路径。远程命令行构建同样只发送文本，并可能从现金余额计费。

本地构建路径已验证：

```bash
bohr auth status --verify
bohr project list
docker build --platform linux/amd64 -t <app>:<tag> <app-directory>
# 以 docker run 调用容器里的 Launching 入口，用样例核对输出。镜像配置了其他 ENTRYPOINT 时显式覆盖。
bohr image push <app>:<tag> <namespace>/<app>:<tag> --project-id <project-id> -o json
```

官方命令行安装和设备授权见[安装文档](https://docs.bohrium.com/docs/bohrctl/install/)。Apple Silicon 上先确认 Docker 能执行 `linux/amd64` 容器。推送完成以回执里的 `status: 1`、`imageUrl` 和 `digest` 为准。开发者中心选择该 `imageUrl` 对应的镜像，使用容器里已验证的绝对入口和解释器路径。示例应用使用 `/app/launching.py` 和 `/usr/local/bin/python3`。

## 验收与余额不足

分别记录镜像推送、App 版本和任务输出。测试页提示余额不足时，查可用的批处理 CPU 机型，用同项目、同镜像、同 Launching 入口验证实际云端计算。可优先用容器内置公开样例，避免运行时依赖额外下载。运行前核对当前定价与项目支持的支付方式。

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
