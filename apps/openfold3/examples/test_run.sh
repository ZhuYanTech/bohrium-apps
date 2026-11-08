#!/usr/bin/env bash
# test_run.sh — OpenFold3 封装的测试。
#
# 只做输入生成、参数映射与输出解析，不做真实预测（无 GPU 时也能跑）。
# 需要：python3 + Launching SDK（~/launching-test-venv），
# SDF 转换需要 OpenBabel 或 RDKit（本机 venv 已装 RDKit）。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 测试用 Python：优先用装了 Launching SDK 的 venv，否则用系统 python3。
if [ -x "$HOME/launching-test-venv/bin/python" ]; then
  PY="$HOME/launching-test-venv/bin/python"
else
  PY="python3"
fi

PASS=0
FAIL=0
SKIP=0

ok()   { PASS=$((PASS+1)); echo "  PASS: $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL: $1"; }
skip() { SKIP=$((SKIP+1)); echo "  SKIP: $1"; }

check() {  # check <描述> <命令...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$desc"; else bad "$desc"; fi
}

expect_fail() {  # expect_fail <描述> <命令...>（预期退出码非 0）
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then bad "$desc（应失败却成功了）"; else ok "$desc"; fi
}

UBQ_FASTA="$SCRIPT_DIR/ubiquitin-1ubq/sequence.fasta"
UBQ_SEQ="MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"

echo "== 1. 蛋白单链试运行（FASTA 文件）=="
"$PY" "$APP_DIR/run_openfold3.py" --protein-sequence-file "$UBQ_FASTA" \
  --out-dir "$TMP/case1" --dry-run >/dev/null 2>&1
check "1.1 试运行退出码 0" test -f "$TMP/case1/query.json"
check "1.2 query.json 是合法 JSON" "$PY" -c \
  "import json; json.load(open('$TMP/case1/query.json'))"
check "1.3 蛋白序列正确（76 残基，A 链）" "$PY" -c "
import json
q = json.load(open('$TMP/case1/query.json'))['queries']['query_1']
p = q['chains'][0]
assert p['molecule_type'] == 'protein' and p['chain_ids'] == 'A', p
assert p['sequence'] == '$UBQ_SEQ', p['sequence']
assert q['use_msas'] is True
assert 'pocket_constraint' not in q
"
check "1.4 runner.yml 默认 cif、无随机种子" "$PY" -c "
t = open('$TMP/case1/runner.yml').read()
assert 'structure_format: cif' in t, t
assert 'seeds' not in t
"

echo "== 2. 复合物试运行（配体 SMILES + 口袋 + DNA/RNA + 修饰）=="
"$PY" "$APP_DIR/run_openfold3.py" --protein-sequence "$UBQ_SEQ" \
  --ligand-smiles CCO --dna-sequence ATGCATGC --rna-sequence AUGCAUGC \
  --modifications "3:SEP,5:MHO" --pocket "B|A:45,A:46|4.0" \
  --model-seeds 2 --diffusion-samples 3 --random-seed 42 \
  --output-format pdb --out-dir "$TMP/case2" --dry-run >/dev/null 2>&1
check "2.1 试运行退出码 0" test -f "$TMP/case2/query.json"
check "2.2 四条链 A/B/C/D 齐全" "$PY" -c "
import json
q = json.load(open('$TMP/case2/query.json'))['queries']['query_1']
types = [(c['molecule_type'], c['chain_ids']) for c in q['chains']]
assert types == [('protein','A'),('ligand','B'),('dna','C'),('rna','D')], types
assert q['chains'][1]['smiles'] == 'CCO'
assert q['chains'][2]['sequence'] == 'ATGCATGC'
assert q['chains'][3]['sequence'] == 'AUGCAUGC'
assert q['chains'][0]['non_canonical_residues'] == {'3':'SEP','5':'MHO'}
assert q['pocket_constraint'] == {'ligand_chain_id':'B','pocket_residues':[['A',45],['A',46]],'max_distance':4.0}
"
check "2.3 runner.yml：pdb、随机种子 42、口袋采样开" "$PY" -c "
t = open('$TMP/case2/runner.yml').read()
assert 'structure_format: pdb' in t, t
assert '- 42' in t, t
assert 'pocket_sampling' in t and 'enabled: true' in t
"

echo "== 3. PDB 文件提取（SEQRES 与 ATOM 两条路径）=="
"$PY" "$APP_DIR/run_openfold3.py" \
  --pdb-file "$SCRIPT_DIR/ubiquitin-1ubq/ubiquitin-seqres.pdb" \
  --out-dir "$TMP/case3" --dry-run >/dev/null 2>&1
check "3.1 SEQRES 提取出 76 残基泛素" "$PY" -c "
import json
q = json.load(open('$TMP/case3/query.json'))['queries']['query_1']
assert q['chains'][0]['sequence'] == '$UBQ_SEQ'
"
"$PY" "$APP_DIR/run_openfold3.py" \
  --pdb-file "$SCRIPT_DIR/ubiquitin-1ubq/tiny-atom.pdb" \
  --out-dir "$TMP/case3b" --dry-run >/dev/null 2>&1
check "3.2 ATOM CA 提取出 MQI" "$PY" -c "
import json
q = json.load(open('$TMP/case3b/query.json'))['queries']['query_1']
assert q['chains'][0]['sequence'] == 'MQI'
"

echo "== 4. SDF 转换（乙醇 → CCO）=="
if command -v obabel >/dev/null 2>&1 || "$PY" -c "import rdkit" 2>/dev/null; then
  "$PY" "$APP_DIR/run_openfold3.py" --protein-sequence "$UBQ_SEQ" \
    --ligand-sdf-file "$SCRIPT_DIR/ubiquitin-1ubq/ethanol.sdf" \
    --out-dir "$TMP/case4" --dry-run >/dev/null 2>&1
  check "4.1 SDF 转成 SMILES CCO" "$PY" -c "
import json
q = json.load(open('$TMP/case4/query.json'))['queries']['query_1']
assert q['chains'][1]['smiles'] == 'CCO', q['chains'][1]
"
else
  skip "4.1 SDF 转换（本机既无 OpenBabel 也无 RDKit）"
fi

echo "== 5. MSA 三条分支 =="
"$PY" "$APP_DIR/run_openfold3.py" --protein-sequence "$UBQ_SEQ" \
  --msa-file "$SCRIPT_DIR/ubiquitin-1ubq/ubiquitin.a3m" \
  --out-dir "$TMP/case5a" --dry-run >/dev/null 2>&1
check "5.1 自备 .a3m：main_msa_file_paths 已填" "$PY" -c "
import json
q = json.load(open('$TMP/case5a/query.json'))['queries']['query_1']
assert q['chains'][0]['main_msa_file_paths'].endswith('ubiquitin.a3m'), q
assert q['use_msas'] is True
"
"$PY" "$APP_DIR/run_openfold3.py" --protein-sequence "$UBQ_SEQ" --no-msa \
  --out-dir "$TMP/case5b" --dry-run >/dev/null 2>&1
check "5.2 --no-msa：use_msas 为 false" "$PY" -c "
import json
q = json.load(open('$TMP/case5b/query.json'))['queries']['query_1']
assert q['use_msas'] is False
assert 'main_msa_file_paths' not in q['chains'][0]
"
"$PY" "$APP_DIR/run_openfold3.py" --protein-sequence "$UBQ_SEQ" \
  --out-dir "$TMP/case5c" --dry-run >/dev/null 2>&1
check "5.3 默认：use_msas 为 true（自动生成）" "$PY" -c "
import json
q = json.load(open('$TMP/case5c/query.json'))['queries']['query_1']
assert q['use_msas'] is True
"

echo "== 6. 输入校验（应失败，退出码 2）=="
expect_fail "6.1 蛋白序列含非法字符 B" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "MQIFB" --out-dir "$TMP/e1" --dry-run
expect_fail "6.2 蛋白序列为空" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "" --out-dir "$TMP/e2" --dry-run
expect_fail "6.3 DNA 序列含 U" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --dna-sequence "AUGC" --out-dir "$TMP/e3" --dry-run
expect_fail "6.4 RNA 序列含 T" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --rna-sequence "ATGC" --out-dir "$TMP/e4" --dry-run
expect_fail "6.5 口袋约束无配体" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --pocket "B|A:45|4.0" --out-dir "$TMP/e5" --dry-run
expect_fail "6.6 口袋残基号超出蛋白长度" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --ligand-smiles CCO --pocket "B|A:999|4.0" \
  --out-dir "$TMP/e6" --dry-run
expect_fail "6.7 口袋配体链不是 B" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --ligand-smiles CCO --pocket "C|A:45|4.0" \
  --out-dir "$TMP/e7" --dry-run
expect_fail "6.8 修饰位置超出蛋白长度" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --modifications "999:SEP" --out-dir "$TMP/e8" --dry-run
expect_fail "6.9 修饰格式不对" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --modifications "3-SEP" --out-dir "$TMP/e9" --dry-run
expect_fail "6.10 蛋白两种来源并存" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --pdb-id 1UBQ --out-dir "$TMP/e10" --dry-run
expect_fail "6.11 配体两种来源并存" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --ligand-smiles CCO \
  --ligand-sdf-file "$SCRIPT_DIR/ubiquitin-1ubq/ethanol.sdf" \
  --out-dir "$TMP/e11" --dry-run
expect_fail "6.12 模型种子数 0" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --model-seeds 0 --out-dir "$TMP/e12" --dry-run
expect_fail "6.13 模型种子数 6" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --model-seeds 6 --out-dir "$TMP/e13" --dry-run
expect_fail "6.14 扩散样本数 0" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --diffusion-samples 0 --out-dir "$TMP/e14" --dry-run
expect_fail "6.15 扩散样本数 11" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --diffusion-samples 11 --out-dir "$TMP/e15" --dry-run
expect_fail "6.16 --msa-file 与 --no-msa 并存" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --msa-file "$SCRIPT_DIR/ubiquitin-1ubq/ubiquitin.a3m" \
  --no-msa --out-dir "$TMP/e16" --dry-run
expect_fail "6.17 SMILES 圆括号不配对" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --ligand-smiles "CC(O" --out-dir "$TMP/e17" --dry-run
expect_fail "6.18 SMILES 含空格" "$PY" "$APP_DIR/run_openfold3.py" \
  --protein-sequence "$UBQ_SEQ" --ligand-smiles "CC O" --out-dir "$TMP/e18" --dry-run

echo "== 7. PDB 编号取数（需联网到 RCSB）=="
if curl -fsSI --max-time 15 "https://www.rcsb.org/fasta/entry/1UBQ" >/dev/null 2>&1; then
  "$PY" "$APP_DIR/run_openfold3.py" --pdb-id 1UBQ \
    --out-dir "$TMP/case7" --dry-run >/dev/null 2>&1
  check "7.1 PDB 编号 1UBQ 取回 76 残基泛素" "$PY" -c "
import json
q = json.load(open('$TMP/case7/query.json'))['queries']['query_1']
assert q['chains'][0]['sequence'] == '$UBQ_SEQ'
"
else
  skip "7.1 PDB 编号 1UBQ（无法访问 RCSB）"
fi

echo "== 8. 输出解析（示例置信度数据）=="
PARSE_DIR="$TMP/parse"
mkdir -p "$PARSE_DIR/query_1/seed_42"
for n in 1 2 3; do
  cp "$SCRIPT_DIR/ubiquitin-1ubq/canned/query_1_seed_42_sample_${n}_confidences_aggregated.json" \
     "$PARSE_DIR/query_1/seed_42/"
  : > "$PARSE_DIR/query_1/seed_42/query_1_seed_42_sample_${n}_model.cif"
done
"$PY" - <<PYEOF
import sys
sys.path.insert(0, "$APP_DIR")
from pathlib import Path
from run_openfold3 import collect_outputs, write_report
out = Path("$PARSE_DIR")
summary = {
    "protein_len": 76,
    "protein_source": "粘贴的序列",
    "composition": "蛋白 76 个残基（A 链）",
    "model_seeds": 1,
    "diffusion_samples": 3,
    "output_format": "cif",
    "pocket_desc": "",
    "random_seed": 42,
}
rows, structure_file, missing = collect_outputs(out, "cif")
assert len(rows) == 3, rows
assert rows[0]["sample"] == 2 and abs(rows[0]["avg_plddt"] - 91.5) < 1e-9, rows[0]
assert rows[1]["sample"] == 1 and rows[2]["sample"] == 3, rows
assert rows[2]["has_clash"] == 1.0, rows[2]
assert structure_file == "predicted.cif"
assert (out / "predicted.cif").exists()
assert (out / "summary.csv").exists()
assert (out / "openfold3_raw").exists()
assert missing == "", missing
write_report(out, summary, rows, "自动生成（https://api.colabfold.com）", True, [])
report = (out / "report_zh.md").read_text(encoding="utf-8")
for needle in ("91.50", "pLDDT", "pTM", "ipTM", "不预测结合亲和力",
               "query_1_seed_42_sample_2_model.cif"):
    assert needle in report, needle
print("parse checks OK")
PYEOF
check "8.1 解析示例数据：排序、CSV、报告均正确" test -f "$PARSE_DIR/report_zh.md"
check "8.2 summary.csv 有 3 行数据、首行是样本 2" "$PY" -c "
import csv
rows = list(csv.DictReader(open('$PARSE_DIR/summary.csv', encoding='utf-8-sig')))
assert len(rows) == 3, rows
assert rows[0]['sample'] == '2' and rows[0]['avg_plddt'] == '91.50', rows[0]
assert rows[2]['has_clash'] == '1', rows[2]
"

echo "== 9. Launching 入口 =="
check "9.1 launching.py -p 退出码 0" "$PY" "$APP_DIR/launching.py" -p

echo ""
echo "结果：$PASS 通过，$FAIL 失败，$SKIP 跳过（共 $((PASS+FAIL+SKIP)) 项）"
[ "$FAIL" -eq 0 ]
