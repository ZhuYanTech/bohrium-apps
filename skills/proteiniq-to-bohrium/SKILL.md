---
name: proteiniq-to-bohrium
description: Select popular ProteinIQ tools and create, resume, or update Bohrium offline Apps with one independently built image per App. Use for catalog deduplication, feature parity audits, bilingual developer documentation, and verified deployments in ZhuYanTech/bohrium-apps.
---

# 将 ProteinIQ 工具部署到玻尔

## 筛选与查重

通过 Ego Lite 打开 ProteinIQ 工具目录，选择 **Most used**，记录实际名次、采集日期、工具链接和主要用途。若排名不可见，记录可用的排序依据。按热度从高到低查重，查玻尔公开 App 广场、开发者已有记录和 GitHub 的 `apps/`。查询英文名、常用简称、中文译名与上游工具名。发现疑似重复时打开详情，比较算法、输入和用途。记录「未检出等价 App」的检索范围和证据。优先选择有明确开源实现、可独立运行、具备可复现样例的高热度工具。

用户要求分批创建时，按 [批量筛选与验收记录](references/batch-acceptance.md) 跟踪每个候选、跳过理由和已完成步骤。用户暂停或只要求审计时，保留记录，等其要求继续创建。

## 对齐、构建和部署

1. 先读来源工具的实际表单和帮助，再对照[兼容性验收清单](https://github.com/ZhuYanTech/bohrium-apps/blob/main/apps/COMPATIBILITY-ACCEPTANCE.md)。记录输入格式与数量、必填和互斥条件、参数默认值和模式、输出结构、数值精度及无结果的含义。已有 App 优先复现影响结果的差异。用同一份样例做对照，区分来源实测、来源文档和当前实现证据。
2. 在 `apps/<slug>/` 保存计算入口、`launching.py`、Dockerfile、应用元数据、样例及双语正文。运行正例、无效输入和必要的混合批次。单独验证每项承诺的格式、模式和参数。汇总明确区分通过、失败与未评估。诊断开关只增加明细时，用同一输入比较开关前后汇总。运行 Launching 并用 `--gen-schema` 检查字段声明。
3. **每个 App 使用独立镜像仓库和自行构建的专属镜像。** 发布前核对项目与当前配额。续做时可复用同一 App 已验证的镜像，新增功能使用该 App 仓库下的新版本标签。分别核对项目自定义镜像、开发者镜像版本、开发者 App 版本。空仓库只表示名称已创建。先本地验证容器再推送。提交结果未知时先回查同名记录。
4. 先确认项目镜像可用并绑定开发者镜像版本，再给 App 绑定该专属镜像。用具体版本的「查看测试链接」检查真实的上传类型、选择器、单行/多行输入和默认值。参数声明与网页呈现可能有差异。用样例完成运行，下载产物并核对数值、行列和状态。用户只要求创建时，按测试版本交付。公开上架按用户要求处理。
5. 将代码、镜像构建配置、双语正文、验证结果及剩余差异推送到指定 GitHub 仓库。记录源码提交、镜像摘要、App 版本、测试任务及输出。批量任务按已授权的范围逐个核验，在记录中区分部署完成和仍待处理的项目。

## 补全开发者页面

镜像和 App 分别填写中英文简述、相关标签、中文和英文介绍、中文和英文帮助。介绍交代算法目的、输入决定的模式和解释边界；帮助写实际文件格式、配置和结果文件，并给一个可复现的样例。以来源页校对算法和示例，以部署版本为准核对输入与输出。来源页额外支持的操作只在确有必要时说明差异。按用户要求，玻尔页面的「来源」只链接开源 GitHub 仓库，许可证核对实际打包版本随附的 LICENSE，并与上游仓库交叉验证。

用 Ego Lite 编辑时分别保存每个语言页。替换正文时先清空编辑器并确认旧内容已移除，再粘贴全文，对照完整内容后保存。每个语言页保存后先单独重开验证内容持久化；预览即时回显不能替代刷新验收。只检查开头可能漏掉残留模板或重复段落。从页面点击目标栏目并核对面板标题。镜像帮助和 App 帮助使用不同页面参数。切换栏目后等当前编辑器或文档加载完成，遇到白屏先回到相同栏目并检查上次保存的内容。最后刷新，逐页核对描述、标签、八份文档、示例数值和来源链接。可以把双语正文保存在应用的 `bohrium/docs/`，参考 [PoseBusters 文档](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters/bohrium/docs)。

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

分别记录容器本地测试、镜像推送、App 表单提交、批处理任务及结果下载。测试页提示余额不足时，查可用的批处理 CPU 机型，用同项目、同镜像、同 Launching 入口验证实际云端计算。可优先用容器内置公开样例，避免运行时依赖额外下载。运行前核对当前定价与项目支持的支付方式。批处理使用相同镜像和入口，优先覆盖表单将传入的参数组合。

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
