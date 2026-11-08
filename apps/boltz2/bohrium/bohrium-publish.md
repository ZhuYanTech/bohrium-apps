# 玻尔（Bohrium）发布清单

> 本 App 现位于 `bohrium-apps` 单一仓库的 `apps/boltz2/` 目录下（仓库：https://github.com/ZhuYanTech/bohrium-apps）。
> 以下命令均在 `apps/boltz2/` 目录内执行。

> 原则：玻尔有自己的计算引擎。我们只创建/发布应用，用户在玻尔上自己开
> GPU 节点、用玻尔算力跑，算力费由用户付给玻尔。本仓库不调用任何第三方
> API（MSA 自动生成除外，用的是公开 ColabFold 服务器），不含任何密钥。

## 前置条件（发布者本人完成）

- [ ] 有玻尔账号（先确定账号主体，再建项目）
- [ ] 在玻尔控制台创建一个项目，记下 `project-id`（数字）
- [ ] 装好 Node.js + `bohr` CLI，并在终端登录（不要把凭证写进仓库）：
  ```bash
  npm install -g @dptech-corp/bohr-cli@latest
  bohr --version
  bohr auth login
  bohr doctor
  ```
  参考：dptech-corp/bohrium-skills（GitHub）里的 `bohrium-setup` 指引。
- [ ] 装好 Docker（构建镜像用；构建机不需要 GPU，但需约 15 GB 磁盘，
  且构建时要能访问 Hugging Face 以下载 6.2 GB 权重）

## 发布步骤

### 1. 构建并推送镜像

```bash
cd apps/boltz2
docker build -t zhuyan/boltz2-bohrium-app:1.0 .

# 用 bohr CLI 在玻尔上登记镜像（把 <project_id> 换成你的项目 ID）
bohr image build --mode local \
  --dockerfile ./Dockerfile --context . \
  --name zhuyan/boltz2-bohrium-app:1.0 \
  --project-id <project_id> -o json
# 上一条命令会返回 pushCommand，在同一个 Docker 环境里原样执行它，
# 不要自己拼 registry 地址。成功后核对返回的 imageUrl、digest、status=1。
```

### 2. 先在玻尔上跑一次任务（不上架，先自测）

```bash
bohr job --help   # 按指引提交一次任务，镜像地址用上一步的 imageUrl
# 输入：KRAS G12C 序列 + 索托拉西布 SMILES（见 examples/kras-g12c-sotorasib/）；
# 期望输出：predicted.pdb、confidence.json、affinity.json、report_zh.md 齐全，
# 且报告含“结合概率”与“预测亲和力”两节。先对上本地试运行的 YAML，再上架。
```

在玻尔上运行时，重点看 MSA 是否自动生成成功。玻尔节点若无法
访问公开 ColabFold 服务器（api.colabfold.com），任务会在 MSA 一步失败；
此时改传自备 `.a3m`（`--msa-file`），或在 App 说明里写明须上传 `.a3m`。

### 3. 在开发者中心创建 App

- 打开 https://www.bohrium.com/developer
- 新建 App，类型选“标准离线任务”，元数据见本目录的 `app.json`
  （名称、描述、输入/输出 schema）
- 关联上一步的镜像地址，EntryPoint 填 `/app/launching.py`，
  填中文使用说明（可直接用仓库 README 的“输入/输出”与“亲和力怎么读”两节）
- 审核要点（玻尔开发者中心协议）：App 须为自行开发或有管理权限的内容，
  不得侵犯第三方知识产权；Boltz-2 本身是 MIT，App 页面须保留 Boltz-2 的
  引用和许可说明（`app.json` 里已写好，发布时不要删）。

### 4. 上架后验收

- [ ] 用玻尔账号打开 App，填 KRAS G12C 序列 + 索托拉西布 SMILES
- [ ] 任务完成，下载 predicted.pdb、confidence.json、affinity.json、report_zh.md，
  对数：报告含结合概率与预测 log10(IC50)，并含换算表
- [ ] 再测一个自己的靶点与配体，确认中文报告可读、警告文案完整

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| 任务在 MSA 一步失败 | 玻尔节点可能无法访问公开 ColabFold 服务器；改传自备 `.a3m`，或检查节点出网 |
| 任务很快失败、无报告 | 多半是序列含非法字符、SMILES 格式不对，或配体超大；先在本地跑 `--dry-run` 对照 |
| 任务退出码 0 但无输出文件 | 显存不足的静默失败；封装已按缺失输出判失败。换更小结构、减少样本数，或换更大显存机型 |
| 亲和力文件缺失，但结构已生成 | 配体可能超过 128 个重原子（只做结构），或亲和力模型未输出；看 report_zh.md 的缺失说明 |
| 镜像推送失败 | 检查 `bohr auth login` 是否过期、project-id 是否对、Docker 是否在同一环境 |
| 构建时下载权重失败 | 构建机需能访问 Hugging Face；换网络或代理后重建 |

## 不做的事

- 不把任何 API Key、账号密码放进镜像、代码或 `app.json`；登录由发布者本人在终端完成。
- 不在玻尔 App 里调用任何第三方 API（MSA 自动生成用的公开 ColabFold 服务器除外）。
- 不用 Boltz-2.1：2.1 只走托管 API，不在 MIT 发布范围内。
