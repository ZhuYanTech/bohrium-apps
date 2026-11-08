#!/usr/bin/env bash
# test_run.sh — Boltz-2 玻尔 App 的本地验证脚本
#
# 用法（在 apps/boltz2/ 目录内）：
#   bash examples/test_run.sh
#   BOLTZ_CMD=boltz bash examples/test_run.sh   # 指定 Boltz 可执行文件
#
# 做的事（全部无 GPU、无网络可跑，不实际预测）：
#   1. 试运行 KRAS G12C + 索托拉西布：生成 input.yaml，检查内容
#   2. 重原子计数：索托拉西布 41 个、咖啡因 14 个
#   3. 错误用例：空序列、非法字符、超过 2900 个残基、SMILES 非法、
#      SMILES 与 CCD 同时提供、.a3m 与 --no-msa 同时提供、缺配体，
#      都应以退出码 2 优雅失败
#   4. 超大配体（150 个重原子）：试运行退出码 0，但只做结构、不算亲和力
#   5. MSA 三分支：默认（自动生成）、上传 .a3m、--no-msa 单序列，
#      生成的 YAML 各不相同
#   6. 输出解析：用解析测试 JSON 生成中文报告，检查换算与警告文案
#   7. Launching 入口：python3 launching.py -p（须装 dp-launching-app，
#      未装时跳过并说明）
#   8. 输出收集：按 Boltz 2.2.1 的真实目录结构
#      boltz_results_<stem>/predictions/<stem>/ 放置假输出，
#      检查 collect_outputs 能收齐结构、置信度、亲和力
set -u
cd "$(dirname "$0")/.."

OUT="${TEST_OUT:-/tmp/boltz2-test-run}"
PASS=0; FAIL=0

ok()   { echo "  ✅ $1"; PASS=$((PASS+1)); }
bad()  { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

SEQ="examples/kras-g12c-sotorasib/sequence.txt"
SMI="$(cat examples/kras-g12c-sotorasib/ligand.smi)"

echo "== 1. 试运行：KRAS G12C + 索托拉西布 =="
rm -rf "$OUT"
if python3 run_boltz2.py --sequence-file "$SEQ" --ligand-smiles "$SMI" \
    --out-dir "$OUT" --dry-run > /tmp/boltz2-test-run.log 2>&1; then
  ok "run_boltz2.py --dry-run 退出码 0"
else
  bad "试运行退出码非 0，见 /tmp/boltz2-test-run.log"
fi
if [ -f "$OUT/input.yaml" ]; then ok "生成了 input.yaml"; else bad "缺少 input.yaml"; fi
grep -q "smiles:" "$OUT/input.yaml" 2>/dev/null && ok "YAML 含配体 SMILES" || bad "YAML 缺少 SMILES"
grep -q "binder: B" "$OUT/input.yaml" 2>/dev/null && ok "YAML 含亲和力 binder: B" || bad "YAML 缺少亲和力声明"
grep -q "msa: empty" "$OUT/input.yaml" 2>/dev/null && bad "默认分支 YAML 不应含 msa: empty" || ok "默认分支 YAML 无 msa: empty（走自动生成）"
grep -q "MTEYKLVVVGACGVGKS" "$OUT/input.yaml" 2>/dev/null && ok "YAML 含 KRAS G12C 序列（G12C）" || bad "YAML 序列不对"

echo "== 2. 重原子计数 =="
python3 - "$SMI" <<'EOF' > /tmp/boltz2-count.log 2>&1
import sys
sys.path.insert(0, ".")
from run_boltz2 import count_heavy_atoms
for smi, want in [(sys.argv[1], 41),
                  ("Cn1cnc2c1c(=O)n(C)c(=O)n2C", 14)]:
    n, method = count_heavy_atoms(smi)
    assert n == want, f"{smi}: got {n}, want {want}"
    print(f"OK {n} ({method})")
EOF
if [ $? -eq 0 ]; then ok "索托拉西布 41 个、咖啡因 14 个"; else bad "重原子计数不对，见 /tmp/boltz2-count.log"; fi

echo "== 3. 错误用例（应退出码 2）=="
check_err() {  # $1=描述 $2..=命令
  local desc="$1"; shift
  python3 run_boltz2.py "$@" --out-dir /tmp/boltz2-test-err >/dev/null 2>&1
  [ $? -eq 2 ] && ok "$desc → 退出码 2" || bad "$desc 退出码不是 2"
}
check_err "空序列" --sequence "" --ligand-smiles "$SMI"
check_err "非法字符（B）" --sequence "ACDEBFGHIK" --ligand-smiles "$SMI"
check_err "超过 2900 个残基" --sequence "$(python3 -c "print('A'*2901)")" --ligand-smiles "$SMI"
check_err "SMILES 方括号未闭合" --sequence-file "$SEQ" --ligand-smiles "C[C"
check_err "SMILES 与 CCD 同时提供" --sequence-file "$SEQ" --ligand-smiles "$SMI" --ligand-ccd ATP
check_err ".a3m 与 --no-msa 同时提供" --sequence-file "$SEQ" --ligand-smiles "$SMI" \
  --msa-file examples/kras-g12c-sotorasib/kras-g12c.a3m --no-msa
check_err "缺配体" --sequence-file "$SEQ"

echo "== 4. 超大配体（150 个重原子，应只做结构） =="
BIGSMI="$(python3 -c "print('C'*150)")"
if python3 run_boltz2.py --sequence-file "$SEQ" --ligand-smiles "$BIGSMI" \
    --out-dir /tmp/boltz2-test-big --dry-run > /tmp/boltz2-test-big.log 2>&1; then
  ok "试运行退出码 0"
  grep -q "只做结构" /tmp/boltz2-test-big.log && ok "提示只做结构、不算亲和力" || bad "缺少超大配体提示"
  grep -q "affinity:" /tmp/boltz2-test-big/input.yaml 2>/dev/null && bad "超大配体 YAML 不应含亲和力" || ok "超大配体 YAML 无亲和力声明"
else
  bad "超大配体试运行退出码非 0"
fi

echo "== 5. MSA 三分支 =="
if python3 run_boltz2.py --sequence-file "$SEQ" --ligand-smiles "$SMI" \
    --msa-file examples/kras-g12c-sotorasib/kras-g12c.a3m \
    --out-dir /tmp/boltz2-test-msa --dry-run >/dev/null 2>&1; then
  grep -q "msa: " /tmp/boltz2-test-msa/input.yaml && ok "上传 .a3m 分支：YAML 含 msa 路径" || bad "上传 .a3m 分支 YAML 缺少 msa"
else
  bad "上传 .a3m 分支试运行失败"
fi
if python3 run_boltz2.py --sequence-file "$SEQ" --ligand-smiles "$SMI" \
    --no-msa --out-dir /tmp/boltz2-test-nomsa --dry-run > /tmp/boltz2-test-nomsa.log 2>&1; then
  grep -q "msa: empty" /tmp/boltz2-test-nomsa/input.yaml && ok "单序列分支：YAML 含 msa: empty" || bad "单序列分支 YAML 缺少 msa: empty"
  grep -q "未使用 MSA" /tmp/boltz2-test-nomsa.log && ok "单序列分支提示精度可能下降" || bad "单序列分支缺少提示"
else
  bad "单序列分支试运行失败"
fi

echo "== 6. 输出解析：解析测试 JSON 生成中文报告 =="
python3 - <<'EOF' > /tmp/boltz2-parse.log 2>&1
import sys
from pathlib import Path
sys.path.insert(0, ".")
from run_boltz2 import parse_affinity, parse_confidence, write_report, affinity_to_ic50_um
base = Path("examples/kras-g12c-sotorasib/canned")
conf = parse_confidence(base / "confidence.json")
aff = parse_affinity(base / "affinity.json")
assert abs(conf["confidence_score"] - 0.8367) < 1e-9
assert abs(aff["affinity_pred_value"] - 0.8367) < 1e-9
assert abs(affinity_to_ic50_um(0.0) - 1.0) < 1e-9
assert abs(affinity_to_ic50_um(-3.0) - 0.001) < 1e-9
out = Path("/tmp/boltz2-test-parse")
out.mkdir(exist_ok=True)
summary = {"sequence_len": 189, "ligand_desc": "SMILES（重原子 41 个）",
           "diffusion_samples": 1, "recycling_steps": 3, "sampling_steps": 200,
           "step_scale": 1.5, "affinity_samples": 5, "affinity_steps": 200,
           "pocket_desc": "", "structure_file": "predicted.pdb"}
write_report(out, summary, conf, aff, "自动生成（https://api.colabfold.com）",
             "", [], True)
print("OK report written")
EOF
if [ $? -eq 0 ]; then ok "解析测试 JSON 成功，换算正确"; else bad "解析测试失败，见 /tmp/boltz2-parse.log"; fi
grep -q "结合概率" /tmp/boltz2-test-parse/report_zh.md 2>/dev/null && ok "中文报告含结合概率" || bad "中文报告缺少结合概率"
grep -q "0.8367" /tmp/boltz2-test-parse/report_zh.md 2>/dev/null && ok "中文报告含亲和力数值" || bad "中文报告缺少亲和力数值"
grep -q "不是实验测得的" /tmp/boltz2-test-parse/report_zh.md 2>/dev/null && ok "中文报告含注意事项" || bad "中文报告缺少注意事项"

echo "== 7. Launching 入口 =="
if python3 -c "import dp.launching" 2>/dev/null; then
  if python3 launching.py -p > /tmp/boltz2-launching-p.log 2>&1; then
    ok "launching.py -p 退出码 0（生成 JSON Schema 预览）"
  else
    bad "launching.py -p 失败，见 /tmp/boltz2-launching-p.log"
  fi
else
  echo "  （跳过：本机未装 dp-launching-app，见 VERIFICATION.md）"
fi

echo "== 8. 输出收集：Boltz 2.2.1 真实目录结构 =="
python3 - <<'EOF' > /tmp/boltz2-collect.log 2>&1
import shutil, sys
from pathlib import Path
sys.path.insert(0, ".")
from run_boltz2 import collect_outputs
base = Path("examples/kras-g12c-sotorasib/canned")
out = Path("/tmp/boltz2-test-collect")
shutil.rmtree(out, ignore_errors=True)
# 按 Boltz 2.2.1 的真实布局放置假输出
pred = out / "boltz_results_input" / "predictions" / "input"
pred.mkdir(parents=True)
shutil.copy2(base / "confidence.json", pred / "confidence_input_model_0.json")
shutil.copy2(base / "affinity.json", pred / "affinity_input.json")
(pred / "input_model_0.pdb").write_text("HEADER fake\n")
conf, aff, struct, note = collect_outputs(out, "input", "pdb", True)
assert struct == "predicted.pdb", struct
assert (out / "predicted.pdb").exists()
assert (out / "confidence.json").exists()
assert (out / "affinity.json").exists()
assert conf is not None and aff is not None
assert note == "", note
print("OK collect_outputs finds boltz_results_input layout")
EOF
if [ $? -eq 0 ]; then ok "按 2.2.1 真实布局收集输出成功"; else bad "输出收集失败，见 /tmp/boltz2-collect.log"; fi

echo ""
echo "结果：通过 $PASS，失败 $FAIL（主输出目录：$OUT）"
[ "$FAIL" -eq 0 ]
