# 蛋白质脂肪族指数

批量计算蛋白质序列的脂肪族指数（Aliphatic Index）。功能参考 [ProteinIQ 工具页](https://proteiniq.io/app/aliphatic-index)，计算采用 [ExPASy 记录的 Ikai 公式](https://web.expasy.org/protparam/protparam-doc.html)。实现独立运行，序列在任务容器内处理。

指数 = 100 × [A + 2.9V + 3.9(I + L)] / N。A、V、I、L 是四种氨基酸在序列中的计数，N 是整条序列的长度。指数范围为 0–390，可用于比较序列组成；单凭指数无法确定热稳定性。

## 输入与输出

- 输入带标题的一条或多条 FASTA 记录，接受 20 种标准氨基酸，字母大小写均可。
- 输出 `aliphatic_index.csv`，每条记录包含编号、长度、四种脂肪族残基计数和指数，按编号排序。编号取标题中第一个空白符或竖线之前的部分。

## 本地运行

```bash
python3 run_aliphatic_index.py examples/example.fasta --out-dir output
bash examples/test_run.sh
```

样例的指数为 100、390、292.5 和 0。容器构建会运行同一组样例以及无效残基检查。

玻尔部署见[发布步骤](bohrium/bohrium-publish.md)。原始文献为 Ikai A. *Thermostability and aliphatic index of globular proteins*. J Biochem. 1980;88(6):1895–1898. DOI 10.1093/oxfordjournals.jbchem.a133168。
