# 校验说明

## 已校验（无 GPU、无 OpenFold3 安装）

- `examples/test_run.sh`：输入生成、参数映射、输出解析、Launching 入口
- `launching.py -p`：返回入口 Schema，退出码 0
- 示例：泛素 1UBQ（76 个残基）序列生成正确的 `query.json`
- 解析示例置信度数据生成 `summary.csv` 与 `report_zh.md`
- 输入校验：非法序列、非法 SMILES、口袋约束、种子/样本数越界均正确拒绝

## 未校验（需 GPU 与玻尔节点）

- 真实预测端到端（需 24 GB 以上显存）
- Docker 镜像构建（约 2.29 GB 检查点 + PyTorch + OpenFold3）
- 玻尔节点能否访问 ColabFold 服务器、RCSB、PubChem
- `setup_openfold` 在检查点已预置时是否跳过重复下载
  （若重复下载，镜像内会出现第二份 `.pt` 文件，构建日志会列出）

## 示例：泛素 1UBQ

- 序列：76 个残基，`examples/ubiquitin-1ubq/sequence.fasta`
- 示例置信度数据：`examples/ubiquitin-1ubq/canned/`，为示例数据，
  用于测试解析逻辑，**不是**本 App 的真实运行结果。
