# 10 个玻尔 App 批量验收

核验于 2026-11-12（UTC+08:00）。按 Protein IQ 的 Most used 排名筛选，核对玻尔 App 广场、开发者已有记录和本仓库。下列工具在实际检索范围内未检出等价应用。来源名称和排名仅用于本验收记录，开发者页面的来源只链接开源 GitHub 仓库。

10 个标准离线 App 均为 1.0.0，绑定各自独立构建的 linux/amd64 镜像。项目镜像和开发者镜像版本均可用，本批新增 10 条项目镜像记录。

## App 广场发布记录

2026-11-13 09:22（UTC+08:00）复核完成。10 个 App 的 1.0.0 版本均显示「已发布」，应用均显示「已上线」。逐个打开公开详情页并按应用名称检索，10 个 App 均可访问且可在广场搜到。

| App 广场详情 | 开发者版本页 | 版本状态 | App 状态 |
| --- | --- | --- | --- |
| [Open Babel 分子格式转换](https://www.bohrium.com/apps/open-babel) | [1.0.0](https://www.bohrium.com/developer/detail/open-babel?tab=versions) | 已发布 | 已上线 |
| [蛋白质拉氏图](https://www.bohrium.com/apps/ramachandran-plot) | [1.0.0](https://www.bohrium.com/developer/detail/ramachandran-plot?tab=versions) | 已发布 | 已上线 |
| [蛋白质亲疏水性曲线](https://www.bohrium.com/apps/hydropathy-plot) | [1.0.0](https://www.bohrium.com/developer/detail/hydropathy-plot?tab=versions) | 已发布 | 已上线 |
| [溶剂可及表面积计算](https://www.bohrium.com/apps/sasa-calculator) | [1.0.0](https://www.bohrium.com/developer/detail/sasa-calculator?tab=versions) | 已发布 | 已上线 |
| [PDB 转 FASTA](https://www.bohrium.com/apps/pdb-to-fasta) | [1.0.0](https://www.bohrium.com/developer/detail/pdb-to-fasta?tab=versions) | 已发布 | 已上线 |
| [文本转 FASTA](https://www.bohrium.com/apps/txt-to-fasta) | [1.0.0](https://www.bohrium.com/developer/detail/txt-to-fasta?tab=versions) | 已发布 | 已上线 |
| [氨基酸三字母转单字母](https://www.bohrium.com/apps/three-to-one) | [1.0.0](https://www.bohrium.com/developer/detail/three-to-one?tab=versions) | 已发布 | 已上线 |
| [蛋白结构 RMSD 计算](https://www.bohrium.com/apps/rmsd-calculator) | [1.0.0](https://www.bohrium.com/developer/detail/rmsd-calculator?tab=versions) | 已发布 | 已上线 |
| [Lipinski 五规则](https://www.bohrium.com/apps/lipinskis-rule-of-5) | [1.0.0](https://www.bohrium.com/developer/detail/lipinskis-rule-of-5?tab=versions) | 已发布 | 已上线 |
| [酶切肽段质量计算](https://www.bohrium.com/apps/peptide-mass) | [1.0.0](https://www.bohrium.com/developer/detail/peptide-mass?tab=versions) | 已发布 | 已上线 |

## 来源表单与结果核验

逐个核对版本测试表单的 75 个输入和设置，文件扩展名与字段声明一致，默认值按类型核对。玻尔把部分枚举呈现为需输入代码的单行文本框。来源结果依据 Protein IQ 页面公开样例和帮助，玻尔结果依据本地及云端实测。扩展名与设置详见各应用目录的帮助文档和字段声明。

| 热度排名和工具 | 玻尔搜索词 | 字段数 | 实测结果 | 当前差异 |
| --- | --- | ---: | --- | --- |
| 1 · [Open Babel](https://proteiniq.io/app/open-babel) | Open Babel、OpenBabel、格式转换 | 10 | 乙醇输出 3 个重原子的 MOL。另测双记录 SMILES → SDF、生成二维坐标和补氢。 | 可选格式为当前镜像支持的子集。最小化步数始终显示，默认 250。 |
| 3 · [Ramachandran plot](https://proteiniq.io/app/ramachandran-plot) | Ramachandran、拉马钱德兰、拉氏图 | 2 | 1UBQ 有 74 个可测残基，均为优选。验证 PNG 和逐残基表，并另用 mmCIF 重跑。 | 增加 PDB 编号入口。按六类 2° 网格分类，下载 CSV 和 PNG。 |
| 8 · [Hydropathy plot](https://proteiniq.io/app/hydropathy-plot) | Hydropathy、亲疏水性曲线、疏水性图 | 4 | MKTAYIAKQR 窗口 5 的六个得分与来源文档一致，首项 −0.44。多条 FASTA 及拒绝偶数窗口均通过。 | 多条文本通过文件上传，输出 CSV 与逐条 PNG。 |
| 9 · [SASA calculator](https://proteiniq.io/app/sasa-calculator) | SASA、溶剂可及表面积 | 3 | 1UBQ 为 4,888.35 Å²、1 链、76 残基。混合 PDB/mmCIF 的 ZIP 在 1.8 Å 下为 4,837.27 Å²，RSA 留空。 | 批量结构用 ZIP。玻尔将 1.4 显示为 1.40。分别下载残基、链、结构 CSV。 |
| 17 · [PDB to FASTA converter](https://proteiniq.io/app/pdb-to-fasta) | PDB to FASTA、PDB 转 FASTA、PDB 提取序列 | 9 | 1UBQ 的 A 链为 76 残基。另测 SEQRES、指定 A 链、短标题、60 字符换行及拒绝不存在的链。 | 在链字段直接输入筛选列表。缺口及修饰残基以布尔项控制。 |
| 25 · [TXT to FASTA converter](https://proteiniq.io/app/txt-to-fasta) | TXT to FASTA、TXT 转 FASTA、文本转 FASTA | 11 | 带编号的文本转换为 MKTAYIA。CSV 测试保留标题与缺口，并记录混入的 RNA 行。 | Word/PDF 需先提取文本，多行用文件上传。 |
| 30 · [Three-to-one converter](https://proteiniq.io/app/three-to-one) | Three-to-one、三字母、氨基酸三字母 | 8 | 催产素示例输出 CYIQNCPLG。另测自定义分隔、括号保留未知、转小写和全部未知时报错。 | 多行用文件上传。另有遇到未知即报错的选项。 |
| 36 · [RMSD calculator](https://proteiniq.io/app/rmsd-calculator) | RMSD、均方根偏差 | 14 | 1UBQ 自比 76 个匹配 Cα，RMSD 约 0 Å。另测 1UBQ 对 1D3Z，首模型 0.5214 Å，全部模式输出 10 对。 | 批量比较结构用 ZIP。提供总体及残基 CSV、变换 JSON 和拟合结构文件。 |
| 42 · [Lipinski's rule of 5](https://proteiniq.io/app/lipinskis-rule-of-5) | Lipinski、五规则、五规则筛选 | 2 | 阿司匹林为 180.16 Da、LogP 1.31、供体 1、受体 3。另测混合 CSV 保留无效项并单独判定两项偏离。 | 单行 SMILES 或文件批量，结果以 CSV 下载。 |
| 51 · [Peptide mass calculator](https://proteiniq.io/app/peptide-mass) | Peptide mass、肽分子量、多肽质量 | 12 | AKR 的 AK 和 R 分别为 218.1499 与 175.1190。另测一次漏切、平均中性质量及按质量排序。 | 多条序列用文件上传。酶切结果为 CSV，反映简化规则。 |

Open Babel 的中文泛词检索返回一个以公式识别为主要用途的助手，未发现等价的分子格式转换功能。

## 部署与产物证据

可通过各 App 目录的发布清单重现容器样例。下列玻尔批处理任务使用 App 版本绑定的项目镜像和相同的 Launching 入口，机型为 c1_m2_cpu，提交时价格为 0.00 元/小时。每项在云端核对输出，下载主结果。下表记录镜像摘要及下载文件 SHA-256。

网页测试页未提供该免费机型，已核对推荐机型 c2_m2_cpu 为 0.16 元/小时、账户现金余额为 0.00 元。网页验收覆盖表单和版本绑定，实际计算用免费批处理完成。

| App / 版本测试页 | 开发者镜像 | 镜像 SHA-256 | 批处理任务 ID | 下载产物和 SHA-256 |
| --- | --- | --- | --- | --- |
| [Open Babel 分子格式转换](https://www.bohrium.com/apps/open-babel/job?type=app&deploymentId=502430&mode=debug) | [open-babel:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/open-babel?tab=versions) | e57806329ba7e9f4fc3395112c17e1cc3aadeda694b88aa14c68c54356d00304 | a68eb1d08eaa4985981f5ac51009422e | converted.mol · a8e5f05d1a51df4d22946b9d7c92cc69703319ffd6caa740f96164d0067177a8 |
| [蛋白质拉氏图](https://www.bohrium.com/apps/ramachandran-plot/job?type=app&deploymentId=502431&mode=debug) | [ramachandran-plot:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/ramachandran-plot?tab=versions) | c1fcbae43ebcf68e566d27884a269b9be388a1322ec4bb62597d82c0d62d71d1 | ebb36a5302ab4c6c98afef88ab1fed1c | ramachandran.csv · ab44a89ba6f01b236a71ee2d6d6011a92dfe9e119e03e69d12ee826f3d8c9417 |
| [蛋白质亲疏水性曲线](https://www.bohrium.com/apps/hydropathy-plot/job?type=app&deploymentId=502429&mode=debug) | [hydropathy-plot:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/hydropathy-plot?tab=versions) | 95649bc54cbbe6187d768dbe4500b016e2bbfd9065f6a29afe4af5f17f06dfd4 | f03eea601aee4f71b73756807b680048 | hydropathy.csv · 10279dd0c44e83e89ca230e3b9307f4cd8a37691a0e527e8151737e075d787fe |
| [溶剂可及表面积计算](https://www.bohrium.com/apps/sasa-calculator/job?type=app&deploymentId=502428&mode=debug) | [sasa-calculator:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/sasa-calculator?tab=versions) | 477788e3a5211210535bd8f8a9e7e17f24db6de6bcd88f6f33eac1ca9beb6ed8 | eac307ab0e324149be5b45601d364f3d | summary.csv · c3c31ca442d5cf06e97c2f0cba405b719d3aae59c09c391e6203a5d4baf2042e |
| [PDB 转 FASTA](https://www.bohrium.com/apps/pdb-to-fasta/job?type=app&deploymentId=502427&mode=debug) | [pdb-to-fasta:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/pdb-to-fasta?tab=versions) | c992613d86195699cf97f658b1ae94584e57242fb62e2ba94dabd32049c0b58d | 93362eaeb81d4c56b679f2dae7aeaa40 | sequences.fasta · c8434e0c2612bc87ef00e9067b8a0da74cfc0cb14761028b2d50c4cbb9f471cb |
| [文本转 FASTA](https://www.bohrium.com/apps/txt-to-fasta/job?type=app&deploymentId=502426&mode=debug) | [txt-to-fasta:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/txt-to-fasta?tab=versions) | bb4a61ba5d0e94cf43ab651cf8c372411e16ce41d63d28885f77c6dfddcdab83 | 930a8eebf60442c088815d03786597cf | sequences.fasta · 1a86c5a2eea56020848be00ed5490497cc753dafbf7ad6a30bedc5c07c5c3667 |
| [氨基酸三字母转单字母](https://www.bohrium.com/apps/three-to-one/job?type=app&deploymentId=502425&mode=debug) | [three-to-one:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/three-to-one?tab=versions) | bf5a28d6dcddeb9fe569e37979fc7fac3f2b7b6bbcf5244aa449a04ed7b34959 | c33d9f170f754a1aa294c2b71d24f31a | converted.txt · 19dd5750a278b2805327e05293214f2e68f77a96f96179ddda322160751d2ab9 |
| [蛋白结构 RMSD 计算](https://www.bohrium.com/apps/rmsd-calculator/job?type=app&deploymentId=502432&mode=debug) | [rmsd-calculator:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/rmsd-calculator?tab=versions) | 71cfdb511b940b8b8f4d69b8b7c3faf2fb32474f3ea29db83cb176712c606b1e | 899c87a1e188457198d632a228010499 | rmsd.csv · 3dd44578fe5359a1fa19eef241dfa69d2004926e4b9ab1882dfc5f372e21c61f |
| [Lipinski 五规则](https://www.bohrium.com/apps/lipinskis-rule-of-5/job?type=app&deploymentId=502433&mode=debug) | [lipinskis-rule-of-5:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/lipinskis-rule-of-5?tab=versions) | c1008ded82f2ee93bcd4c4d2571c9f5542d5cb9446bea6662e1370802a55691c | 4bee9fb866744dcaac11cec1c912c908 | lipinski.csv · 0ab2c4e4f7b8bc5f9a32acccaa72de9ed41f51891e5e7132d6848d73bf10b0d1 |
| [酶切肽段质量计算](https://www.bohrium.com/apps/peptide-mass/job?type=app&deploymentId=502424&mode=debug) | [peptide-mass:1.0.0](https://www.bohrium.com/developer/image-detail/zhuyan-xlab/peptide-mass?tab=versions) | c71e38430033d76c82c3997740e20ed09025706ebbcd3e942dba29291607e40d | ec19e9c555974b2ead3ef98d741c4dd9 | peptides.csv · 69bc0dd1400e46efb9a5aba9cacc0e62da051aac7a7752349ccd72d1e7d7b0c5 |

## PDB 编号输入的云端补测

以下四项在同一免费机型上以 1UBQ 编号取回公开数据并下载产物。

| App | 批处理任务 ID | 结果 |
| --- | --- | --- |
| pdb-to-fasta | c3f1ba352fd3497e9671e15d1c5acc03 | A 链 76 残基 |
| sasa-calculator | faf816293b7f4451b0f6e5d6c5dbf532 | 4,888.35 Å² |
| hydropathy-plot | 63c2ca393be14fc5af01f3ca2a80e975 | 默认窗口的首个值 0.9333 |
| peptide-mass | 4d91d7ac75f94e75bb5925e1ea61e221 | 首个肽段 MQIFVK 为 765.4328 |

## 文档和源码

- 每个镜像和 App 均保存中英文简述及标签，并回读四份 Markdown。80 份介绍及帮助与各目录的 bohrium/docs/ 正文一致。
- [初始封装源码提交](https://github.com/ZhuYanTech/bohrium-apps/commit/3100296)记录计算入口、依赖及样例。构建复用了本地 Launching 公共依赖层和预下载的 Python 依赖包，每个 App 独立复制自己的入口、实现和样例，形成不同镜像摘要。
- [可复用 Skill](../skills/proteiniq-to-bohrium/SKILL.md)记录批量查重、网页表单、双语回读、零价验收及下载方法。
