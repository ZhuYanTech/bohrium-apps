# Bohrium Apps — ZhuYanTech

[English below](#english)

ZhuYanTech 在深势科技玻尔（Bohrium）平台上发布的所有开源应用，都放在这一个仓库里。
**不再按应用各建一个库**：新应用就是 `apps/` 下的一个新目录。

> 原则（不变）：玻尔有自己的计算引擎。我们只做应用、发布镜像；
> 用户在玻尔上自己开节点、用玻尔算力跑，算力费由用户付给玻尔。
> 这里的任何应用都不调用第三方 API，不含任何密钥。

仓库：https://github.com/ZhuYanTech/bohrium-apps

## 应用一览

| 应用 | 说明 | 算力 | 目录 |
| --- | --- | --- | --- |
| **PLIP 蛋白-配体相互作用分析** | 上传蛋白-配体复合物 PDB（或填 PDB ID），输出相互作用清单（CSV）+ 中文报告。单结构通常 5 分钟内完成。 | CPU | [`apps/plip/`](apps/plip/) |
| **PoseBusters 对接姿势质量检查** | 对接或 AI 预测出的配体姿势到底站不站得住：化学有效性、分子内几何、与口袋的相容性、与晶体结构的 RMSD，共 28 项检查，输出汇总表 + 中文报告。通常 1 分钟内完成。 | CPU | [`apps/posebusters/`](apps/posebusters/) |
| **Boltz-2 共折叠与亲和力预测** | 输入蛋白序列 + 配体 SMILES，一次给出复合物结构和结合亲和力（结合概率、预测 log10(IC50)）。 | GPU | [`apps/boltz2/`](apps/boltz2/) |
| **OpenFold3 结构预测** | 输入蛋白序列（可加配体、DNA、RNA），预测复合物三维结构，输出 CIF/PDB + 置信度 + 中文报告。 | GPU | [`apps/openfold3/`](apps/openfold3/) |

典型串法：`boltz2` / `openfold3` 出结构 → `posebusters` 把关姿势质量 →
`plip` 分析通过筛选的姿势的相互作用。中间这一步能挡掉大量无效的后续计算。

各应用的验证记录见各自目录下的 `VERIFICATION.md`：

- PLIP：1VSN 13 个相互作用（氢键 7、疏水 4、卤键 2）；3MXF 的目标配体 JQ1 14 个（含 ASN140 经典氢键）。
  见 [`apps/plip/VERIFICATION.md`](apps/plip/VERIFICATION.md)
- PoseBusters：4 个晶体基准结构 28 项全过；两个人造缺陷姿势分别被对应分组精准抓出；
  配体剥离逻辑与官方预处理文件等价。见 [`apps/posebusters/VERIFICATION.md`](apps/posebusters/VERIFICATION.md)

## 如何加一个新应用

1. 在 `apps/` 下新建目录，名字用小写短横线，如 `apps/<name>/`。
2. 每个应用自成一体，至少包含：
   - `README.md`：这是什么、输入/输出、本地怎么跑、怎么发布到玻尔
   - `Dockerfile`：任务镜像（版本钉死）
   - `bohrium/bohrium-publish.md`：发布清单 + `bohr` 命令
   - `bohrium/app.json`：App 元数据（中英描述、输入/输出 schema）
   - `examples/`：至少一个跑通的例子 + 验证脚本
3. 别在应用之间共用会变的代码；共用的说明只写在仓库根 README 这里。
4. 新应用先在本地验证通过，再推镜像、上架。

## 目录结构

```
.
├── README.md          本文件
├── apps/
│   ├── plip/          PLIP 蛋白-配体相互作用分析（CPU）
│   ├── posebusters/   PoseBusters 对接姿势质量检查（CPU）
│   │   ├── README.md
│   │   ├── VERIFICATION.md
│   │   ├── run_posebusters.py   计算入口（CLI）
│   │   ├── launching.py         玻尔离线任务入口
│   │   ├── examples/            一键验证脚本 + 已验证产物
│   │   └── bohrium/             Dockerfile.imagehub + app.json + 发布清单
│   ├── boltz2/        Boltz-2 共折叠与亲和力预测（GPU）
│   └── openfold3/     OpenFold3 结构预测（GPU）
└── (未来：apps/<下一个应用>/)
```

## 许可 License

- 本仓库的封装代码与文档：MIT License（见仓库根 LICENSE）。
- 各应用依赖的第三方工具按其自身许可使用：PLIP 为 GNU GPLv2，使用时请保留其引用和许可说明（见 `apps/plip/README.md` 的“许可与引用”一节）。

---

<a id="english"></a>
## English

All open-source apps ZhuYanTech publishes on the Deep Potential Bohrium platform live in this single repository.
**No separate repo per app**: a new app is a new folder under `apps/`.

> Standing rule: Bohrium has its own compute engine. We only build and publish apps;
> users run them on Bohrium compute and pay Bohrium. No app here calls any
> third-party API, and no credentials are stored anywhere in this repo.

Repository: https://github.com/ZhuYanTech/bohrium-apps

## Apps

| App | Description | Compute | Directory |
| --- | --- | --- | --- |
| **PLIP protein-ligand interaction profiler** | Upload a protein-ligand complex PDB (or enter a PDB ID) and get an interaction list (CSV) + a Chinese report. | CPU | [`apps/plip/`](apps/plip/) |
| **PoseBusters docking pose validator** | Check whether docked or AI-generated ligand poses are chemically and physically valid: up to 28 checks covering chemical validity, intramolecular geometry, pocket compatibility and RMSD to a crystal pose. | CPU | [`apps/posebusters/`](apps/posebusters/) |
| **Boltz-2 co-folding and affinity** | Protein sequence + ligand SMILES in, complex structure and binding affinity out. | GPU | [`apps/boltz2/`](apps/boltz2/) |
| **OpenFold3 structure prediction** | Protein sequence (optionally with ligands, DNA, RNA) in, complex structure + confidence + Chinese report out. | GPU | [`apps/openfold3/`](apps/openfold3/) |

Typical chain: `boltz2` / `openfold3` produce structures, `posebusters` filters out
implausible poses, `plip` profiles the interactions of what survives.

Verification records live in each app's own `VERIFICATION.md`.

## Adding a new app

1. Create `apps/<name>/` (lowercase, hyphenated).
2. Each app is self-contained and must include at minimum:
   - `README.md` — what it is, inputs/outputs, how to run locally, how to publish to Bohrium
   - `Dockerfile` — the job image, with pinned versions
   - `bohrium/bohrium-publish.md` — publish checklist + `bohr` commands
   - `bohrium/app.json` — App metadata (zh/en description, input/output schema)
   - `examples/` — at least one working example + a test script
3. Don't share mutable code between apps; shared guidance lives only in this root README.
4. Verify a new app locally before pushing an image and publishing.

## License

- Wrapper code and docs in this repo: MIT License (see root LICENSE).
- Third-party tools used by each app keep their own licenses: PLIP is GNU GPLv2 — keep its citation and license notice (see `apps/plip/README.md`).
