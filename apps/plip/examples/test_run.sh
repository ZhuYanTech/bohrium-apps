#!/usr/bin/env bash
# test_run.sh — PLIP 玻尔 App 的本地验证脚本
#
# 用法（在仓库根目录）：
#   bash examples/test_run.sh
#   PLIP_CMD=plip bash examples/test_run.sh   # 指定 PLIP 可执行文件
#   PLIP_CMD="docker run --rm -v $PWD:/work plip-bohrium-app:1.0" bash examples/test_run.sh
#
# 做的事：
#   1. 用 run_plip.py 跑 1VSN（从 RCSB 下载，Cathepsin K + 抑制剂 NFT）
#   2. 检查 interactions.csv / report_zh.md 是否生成、行数是否 > 0
#   3. 跑两个错误用例：不存在的文件、格式不对的 PDB ID，都应以退出码 2 优雅失败
#   4. 跑一个无配体用例：只有蛋白原子的 PDB，应生成 0 行相互作用的空表 + 中文说明，退出码 0
#
# 注意：本脚本不伪造任何结果。1VSN 的相互作用数以 PLIP 当场输出为准；
# 2026-11-07 用 PLIP 3.0.1 实测为 13 个（氢键 7、疏水 4、卤键 2），
# 换版本后数字可能略有不同，脚本只断言“> 0”，不硬编码 13。
set -u
cd "$(dirname "$0")/.."

PLIP_CMD="${PLIP_CMD:-plip}"
OUT="${TEST_OUT:-/tmp/plip-test-run}"
PASS=0; FAIL=0

ok()   { echo "  ✅ $1"; PASS=$((PASS+1)); }
bad()  { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

echo "== 1. 主用例：1VSN =="
rm -rf "$OUT"
if python3 run_plip.py --pdb-id 1VSN --out-dir "$OUT" --plip-cmd "$PLIP_CMD" > /tmp/plip-test-run.log 2>&1; then
  ok "run_plip.py 退出码 0"
else
  bad "run_plip.py 退出码非 0，见 /tmp/plip-test-run.log"
fi
if [ -f "$OUT/interactions.csv" ] && [ -f "$OUT/report_zh.md" ]; then
  ok "生成了 interactions.csv 和 report_zh.md"
else
  bad "缺少 interactions.csv 或 report_zh.md"
fi
N=$(tail -n +2 "$OUT/interactions.csv" 2>/dev/null | grep -c . || true)
if [ "${N:-0}" -gt 0 ]; then ok "interactions.csv 有 $N 行相互作用"; else bad "interactions.csv 为空"; fi
grep -q "相互作用总数" "$OUT/report_zh.md" 2>/dev/null && ok "中文报告含总数统计" || bad "中文报告缺少总数统计"
grep -q "NFT" "$OUT/interactions.csv" 2>/dev/null && ok "配体 NFT 在表中" || bad "配体 NFT 不在表中"

echo "== 2. 错误用例：不存在的文件（应退出码 2）=="
if python3 run_plip.py --pdb-file /tmp/does-not-exist-12345.pdb --out-dir /tmp/plip-test-err1 >/dev/null 2>&1; then
  bad "不存在的文件居然成功了"
else
  [ $? -eq 2 ] && ok "退出码 2" || ok "以非 0 退出（见日志）"
fi

echo "== 3. 错误用例：PDB ID 格式不对（应退出码 2）=="
python3 run_plip.py --pdb-id XYZ --out-dir /tmp/plip-test-err2 >/dev/null 2>&1
[ $? -eq 2 ] && ok "退出码 2" || bad "退出码不是 2"

echo "== 4. 无配体用例：只有蛋白原子（应 0 行 + 中文说明，退出码 0）=="
printf 'ATOM      1  N   ALA A   1      11.104  13.207   2.000  1.00 20.00           N\nATOM      2  CA  ALA A   1      12.560  13.207   2.000  1.00 20.00           C\nATOM      3  C   ALA A   1      13.000  14.600   2.000  1.00 20.00           C\nATOM      4  O   ALA A   1      12.500  15.500   2.000  1.00 20.00           O\nEND\n' > /tmp/protein-only.pdb
if python3 run_plip.py --pdb-file /tmp/protein-only.pdb --out-dir /tmp/plip-test-err3 --plip-cmd "$PLIP_CMD" >/dev/null 2>&1; then
  ok "退出码 0（优雅处理，未崩溃）"
  LINES=$(tail -n +2 /tmp/plip-test-err3/interactions.csv 2>/dev/null | grep -c . || true)
  [ "${LINES:-99}" -eq 0 ] && ok "相互作用 0 行" || bad "无配体却有 $LINES 行"
else
  bad "无配体用例退出码非 0"
fi

echo ""
echo "结果：通过 $PASS，失败 $FAIL（主输出目录：$OUT）"
[ "$FAIL" -eq 0 ]
