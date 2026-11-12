#!/usr/bin/env bash
# examples/test_run.sh — PoseBusters 玻尔 App 的一键验证
#
#   bash examples/test_run.sh
#
# 跑三组：
#   1. 正例：PoseBusters 自带的 4 个晶体结构，配体对自己做 redock，应当 28 项全过
#   2. 反例：由晶体配体造出的两个有缺陷姿势，应当分别在"口袋相容性"和"分子内几何"上失败
#   3. 模式：mol / dock / redock 三种模式的检查项数应当递增
#
# 退出码 0 表示全部符合预期。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$HERE/.."
RUN="python3 $APP/run_posebusters.py"
WORK="${WORK_DIR:-$(mktemp -d)}"
DS="${POSEBUSTERS_DATA:-$(python3 -c 'import posebusters,os;print(os.path.join(os.path.dirname(posebusters.__file__),"datasets","pdb"))')}"

fails=0
ok()   { echo "  ✅ $1"; }
bad()  { echo "  ❌ $1"; fails=$((fails+1)); }

echo "数据集：$DS"
echo "工作目录：$WORK"
echo

echo "== 1. 正例：晶体配体 redock 自己，应 PB-valid 100% =="
for pdb in 1ia1 1of6 1s3v 1uou; do
  L="$DS/$pdb/${pdb}_ligand.sdf"
  P="$DS/$pdb/${pdb}_protein_one_lig_removed.pdb"
  [ -f "$L" ] && [ -f "$P" ] || { echo "  跳过 $pdb（缺数据）"; continue; }
  line=$($RUN --mol-pred "$L" --mol-true "$L" --protein "$P" \
               --out-dir "$WORK/good_$pdb" 2>&1 | grep "^完成" || true)
  if echo "$line" | grep -q "PB-valid 100.0%"; then ok "$pdb — $line"
  else bad "$pdb — 期望 100%，实际：$line"; fi
done
echo

echo "== 2. 反例：人造缺陷姿势，应当被抓出来 =="
python3 "$HERE/make_bad_poses.py" "$DS/1ia1/1ia1_ligand.sdf" "$WORK/bad" >/dev/null
P="$DS/1ia1/1ia1_protein_one_lig_removed.pdb"
L="$DS/1ia1/1ia1_ligand.sdf"

# 2a 平移 10 Å：应在"与口袋相容性 / RMSD"上失败
$RUN --mol-pred "$WORK/bad/bad_translated.sdf" --mol-true "$L" --protein "$P" \
     --out-dir "$WORK/bad_tr" >/dev/null 2>&1
f=$(sed -n '2p' "$WORK/bad_tr/summary.csv" | awk -F, '{print $NF}')
if echo "$f" | grep -q "minimum_distance_to_protein" && echo "$f" | grep -q "rmsd"; then
  ok "平移 10 Å — 蛋白碰撞与 RMSD 均被抓出：$f"
else bad "平移 10 Å — 期望抓出蛋白碰撞与 RMSD，实际：$f"; fi

# 2b 坐标缩 0.5 倍：应在"分子内几何"上失败
$RUN --mol-pred "$WORK/bad/bad_squashed.sdf" --mol-true "$L" --protein "$P" \
     --out-dir "$WORK/bad_sq" >/dev/null 2>&1
f=$(sed -n '2p' "$WORK/bad_sq/summary.csv" | awk -F, '{print $NF}')
if echo "$f" | grep -q "bond_lengths" && echo "$f" | grep -q "internal_steric_clash"; then
  ok "缩 0.5 倍 — 键长与分子内碰撞均被抓出：$f"
else bad "缩 0.5 倍 — 期望抓出键长与分子内碰撞，实际：$f"; fi
echo

echo "== 3. 三种模式的检查项数应递增 =="
n_mol=$($RUN --mol-pred "$L" --out-dir "$WORK/m_mol" 2>&1 | grep -oP '全部 \K\d+')
n_dock=$($RUN --mol-pred "$L" --protein "$P" --out-dir "$WORK/m_dock" 2>&1 | grep -oP '全部 \K\d+')
n_re=$($RUN --mol-pred "$L" --protein "$P" --mol-true "$L" --out-dir "$WORK/m_re" 2>&1 | grep -oP '全部 \K\d+')
echo "  mol=$n_mol  dock=$n_dock  redock=$n_re"
if [ "${n_mol:-0}" -lt "${n_dock:-0}" ] && [ "${n_dock:-0}" -lt "${n_re:-0}" ]; then
  ok "检查项数递增 $n_mol < $n_dock < $n_re"
else bad "检查项数未按 mol < dock < redock 递增"; fi
echo

echo "== 4. 错误处理 =="
# 这两条本来就该失败退出，所以先把输出收进变量，别让退出码干扰判断
out=$($RUN --mol-pred /nonexistent.sdf --out-dir "$WORK/err" 2>&1 || true)
if echo "$out" | grep -q "找不到预测姿势文件"; then
  ok "文件不存在时给出中文提示"
else bad "文件不存在时未给出预期提示，实际：$out"; fi

out=$($RUN --mol-pred "$L" --pdb-id ZZZZ --out-dir "$WORK/err2" 2>&1 || true)
if echo "$out" | grep -q "PDB 编号格式不对"; then
  ok "PDB 编号非法时给出中文提示"
else bad "PDB 编号非法时未给出预期提示，实际：$out"; fi
echo

if [ "$fails" -eq 0 ]; then echo "全部通过。"; else echo "有 $fails 项不符合预期。"; fi
exit "$fails"
