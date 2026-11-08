# 玻尔（Bohrium）发布清单

> 本 App 现位于 `bohrium-apps` 单一仓库的 `apps/plip/` 目录下（仓库：https://github.com/ZhuYanTech/bohrium-apps）。
> 以下命令均在 `apps/plip/` 目录内执行。

> 原则：玻尔有自己的计算引擎。我们只创建/发布应用，用户在玻尔上自己开
> 计算节点、用玻尔算力跑，算力费由用户付给玻尔。本仓库不调用任何第三方
> API，不含任何密钥。

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
- [ ] 装好 Docker（构建镜像用）

## 发布步骤

### 1. 构建并推送镜像

```bash
cd apps/plip
docker build -t plip-bohrium-app:1.0 .

# 用 bohr CLI 在玻尔上登记镜像（把 <project_id> 换成你的项目 ID）
bohr image build --mode local \
  --dockerfile ./Dockerfile --context . \
  --name plip-bohrium-app:1.0 \
  --project-id <project_id> -o json
# 上一条命令会返回 pushCommand，在同一个 Docker 环境里原样执行它，
# 不要自己拼 registry 地址。成功后核对返回的 imageUrl、digest、status=1。
```

### 2. 先在玻尔上跑一次任务（不上架，先自测）

```bash
bohr job --help   # 按指引提交一次任务，镜像地址用上一步的 imageUrl
# 输入：1VSN.pdb；期望输出：interactions.csv 有 13 行（PLIP 3.0.1），
# report_zh.md 含“相互作用总数：13”。先对上本地结果，再上架。
```

### 3. 在开发者中心创建 App

- 打开 https://www.bohrium.com/developer
- 新建 App，元数据见本目录的 `app.json`（名称、描述、输入/输出 schema）
- 关联上一步的镜像地址，填中文使用说明（可直接用仓库 README 的“输入/输出”一节）
- 审核要点（玻尔开发者中心协议）：App 须为自行开发或有管理权限的内容，
  不得侵犯第三方知识产权；PLIP 本身是 GPLv2，App 页面须保留 PLIP 的引用
  和许可说明（`app.json` 里已写好，发布时不要删）。

### 4. 上架后验收

- [ ] 用玻尔账号打开 App，上传 1VSN.pdb 或填 PDB ID `1VSN`
- [ ] 任务完成，下载 interactions.csv、report_zh.md，对数：13 个
- [ ] 再测一个自己的结构（对接结果），确认中文报告可读

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| 任务很快失败、无报告 | 多半是 PDB 里没有配体（HETATM），或文件损坏；先在本地跑 `bash examples/test_run.sh` 对照 |
| 没有 PNG 图片 | 正常。`-y`/`-p` 需要 PyMOL，本镜像故意没装；3D 查看请用 PyMOL 或 Mol* 打开原 PDB |
| 镜像推送失败 | 检查 `bohr auth login` 是否过期、project-id 是否对、Docker 是否在同一环境 |
| 想要 PyMOL 出图 | 需另装 PyMOL，镜像会变大、构建变慢，默认不装 |

## 不做的事

- 不把任何 API Key、账号密码放进镜像、代码或 `app.json`；登录由发布者本人在终端完成。
- 不在玻尔 App 里调用任何第三方 API。
