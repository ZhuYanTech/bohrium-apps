#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_posebusters.py — PoseBusters 对接姿势质量检查（玻尔 App 的计算入口）

做什么：拿对接 / 结构预测生成的配体姿势，逐项检查它在化学和物理上站不站得住，
再输出一张明细表、一张每个姿势一行的汇总表，和一份中文报告。

三种模式（按给了什么输入自动判定）：
  mol    只给预测姿势              —— 只查分子本身（化学有效性 + 分子内几何）
  dock   预测姿势 + 蛋白结构        —— 再查与口袋的相容性（碰撞、体积重叠、是否跑飞）
  redock 预测姿势 + 蛋白 + 晶体配体 —— 再查与参考的一致性和 RMSD ≤ 2 Å

PoseBusters 许可：MIT。本脚本不调用任何第三方 API、不含密钥；
唯一的网络访问是按用户给的 PDB 编号从 RCSB 下载蛋白结构。

引用：
- Buttenschoen, M., Morris, G. M., Deane, C. M. PoseBusters: AI-based docking
  methods fail to generate physically valid poses or generalise to novel sequences.
  Chem. Sci. 15, 3130-3139 (2024). doi:10.1039/D3SC04185A
"""
from __future__ import annotations

import argparse
import csv
from importlib.resources import files
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PRESETS = {"mol", "dock", "redock", "regen", "gen", "mol_fast", "dock_fast",
           "redock_fast", "regen_fast", "gen_fast"}
FORMATS = {"short", "long", "csv"}

RCSB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"

# 检查项 -> (中文名, 分组, 失败时的解读与处理建议)
CHECKS: dict[str, tuple[str, str, str]] = {
    "mol_pred_loaded": ("预测姿势可读取", "A 读取与化学有效性",
        "文件打不开或格式不对。确认是 SDF/MOL/MOL2/PDB，且没有截断。"),
    "mol_true_loaded": ("参考配体可读取", "A 读取与化学有效性",
        "晶体参考配体文件打不开。确认 SDF 完整。"),
    "mol_cond_loaded": ("蛋白结构可读取", "A 读取与化学有效性",
        "蛋白文件打不开。确认 PDB 文件完整，且已去掉要对接的那个配体。"),
    "sanitization": ("化学净化通过", "A 读取与化学有效性",
        "RDKit 认为这个分子化学上非法（价态、芳香性等）。多半是生成模型吐出了不合法结构。"),
    "inchi_convertible": ("可转为 InChI", "A 读取与化学有效性",
        "无法生成 InChI，通常伴随化学净化失败。"),
    "all_atoms_connected": ("原子全部相连", "A 读取与化学有效性",
        "分子断成了几块。常见于生成模型断键，或文件里混进了多个分子。"),
    "no_radicals": ("无自由基", "A 读取与化学有效性",
        "出现未配对电子。通常是加氢或价态推断出错。"),

    "molecular_formula": ("分子式与参考一致", "B 与参考分子的一致性",
        "预测分子和参考配体不是同一个化合物。确认有没有拿错文件，或建模时改变了组成。"),
    "molecular_bonds": ("成键与参考一致", "B 与参考分子的一致性",
        "键的连接方式和参考不同。对接不应改变分子拓扑。"),
    "double_bond_stereochemistry": ("双键立体化学与参考一致", "B 与参考分子的一致性",
        "顺反构型被改了。检查输入时有没有丢失立体信息。"),
    "tetrahedral_chirality": ("四面体手性与参考一致", "B 与参考分子的一致性",
        "手性中心被翻转。对接不应改变手性；常见于从 SMILES 重新生成坐标时丢了手性。"),

    "bond_lengths": ("键长合理", "C 分子内几何",
        "存在明显过长或过短的键。典型的生成模型几何畸变，物理上不成立。"),
    "bond_angles": ("键角合理", "C 分子内几何",
        "键角偏离理论值过多。同上，几何畸变。"),
    "internal_steric_clash": ("分子内无原子碰撞", "C 分子内几何",
        "分子自己的原子挤到一起了。构象不可能存在。"),
    "aromatic_ring_flatness": ("芳环保持共平面", "C 分子内几何",
        "芳环被扭弯了。芳环必须是平面，这是硬性几何约束。"),
    "non-aromatic_ring_non-flatness": ("非芳环未被压平", "C 分子内几何",
        "饱和环（如环己烷）被压成了平面。真实构象应是椅式/船式。"),
    "double_bond_flatness": ("双键周围共平面", "C 分子内几何",
        "双键两端取代基不共面，sp2 杂化被破坏。"),
    "internal_energy": ("内部能量合理", "C 分子内几何",
        "构象能量远高于合理构象系综。姿势虽无明显畸变，但处在高能扭曲状态，实际不会这么结合。"),

    "protein-ligand_maximum_distance": ("配体未脱离蛋白", "D 与口袋的相容性",
        "配体整体跑到蛋白外面去了，没落在口袋里。对接搜索框可能设错了位置。"),
    "minimum_distance_to_protein": ("与蛋白无原子碰撞", "D 与口袋的相容性",
        "配体原子和蛋白原子挤在一起。姿势物理上不可能。"),
    "minimum_distance_to_organic_cofactors": ("与有机辅因子无碰撞", "D 与口袋的相容性",
        "和口袋里的有机辅因子（如 NAD、血红素）撞上了。"),
    "minimum_distance_to_inorganic_cofactors": ("与金属离子无碰撞", "D 与口袋的相容性",
        "和金属离子撞上了。若该配体本就配位金属，可结合实际判断是否放行。"),
    "minimum_distance_to_waters": ("与结晶水无碰撞", "D 与口袋的相容性",
        "和结晶水撞上了。若对接时本应置换该水分子，这一项可酌情忽略。"),
    "volume_overlap_with_protein": ("与蛋白体积重叠不超限", "D 与口袋的相容性",
        "配体体积和蛋白重叠过多，是比原子碰撞更整体的穿模判据。"),
    "volume_overlap_with_organic_cofactors": ("与有机辅因子体积重叠不超限", "D 与口袋的相容性",
        "和有机辅因子大面积穿模。"),
    "volume_overlap_with_inorganic_cofactors": ("与金属离子体积重叠不超限", "D 与口袋的相容性",
        "和金属离子大面积穿模。"),
    "volume_overlap_with_waters": ("与结晶水体积重叠不超限", "D 与口袋的相容性",
        "和结晶水大面积穿模。是否可接受取决于该水是否应被置换。"),

    "rmsd_≤_2å": ("与晶体姿势 RMSD ≤ 2 Å", "E 与晶体结构的吻合度",
        "姿势偏离晶体结构超过 2 Å，按领域惯例算没对准。注意：这一项只在给了晶体参考配体时才有意义。"),
}

GROUP_ORDER = [
    "A 读取与化学有效性",
    "B 与参考分子的一致性",
    "C 分子内几何",
    "D 与口袋的相容性",
    "E 与晶体结构的吻合度",
]

MODE_DESC = {
    "mol": "mol（只给了预测姿势：检查化学有效性与分子内几何）",
    "dock": "dock（预测姿势 + 蛋白：另查与口袋的相容性）",
    "redock": "redock（预测姿势 + 蛋白 + 晶体配体：另查与参考的一致性和 RMSD）",
    "reference_only": "参考配体模式（未提供蛋白，跳过与口袋相容性的检查）",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_pdb(pdb_id: str, dest_dir: Path) -> Path:
    """按 PDB 编号从 RCSB 下载蛋白结构。"""
    pdb_id = pdb_id.strip().upper()
    if len(pdb_id) != 4 or not pdb_id[0].isdigit():
        raise SystemExit(f"PDB 编号格式不对：{pdb_id!r}（应为 4 位，首位为数字，如 1IA1）")
    dest = dest_dir / f"{pdb_id}.pdb"
    url = RCSB_URL.format(pdb_id=pdb_id)
    log(f"从 RCSB 下载 {pdb_id} …")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, dest.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"下载 {pdb_id} 失败：HTTP {exc.code}。确认编号是否存在。") from exc
    except Exception as exc:
        raise SystemExit(f"下载 {pdb_id} 失败：{exc}") from exc
    if dest.stat().st_size < 1000:
        raise SystemExit(f"下载到的 {pdb_id}.pdb 过小，疑似无效。")
    log(f"  已保存 {dest}（{dest.stat().st_size} 字节）")
    return dest


# 这些 HETATM 不算"目标配体"：水、常见金属离子与简单无机离子。
# PoseBusters 会单独检查配体与水、与辅因子的距离，所以它们必须留在蛋白文件里。
NON_LIGAND_HET = {
    "HOH", "DOD", "WAT",
    "NA", "K", "MG", "CA", "ZN", "FE", "FE2", "MN", "CU", "CU1", "CO", "NI", "CD", "HG",
    "CL", "BR", "IOD", "F", "SO4", "PO4", "NO3", "ACT", "EDO", "GOL", "DMS", "PEG", "MPD",
}


def list_het_residues(pdb_path: Path) -> dict[str, int]:
    """统计 PDB 里各 HETATM 残基名的原子数。"""
    counts: dict[str, int] = {}
    with pdb_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("HETATM"):
                name = line[17:20].strip()
                counts[name] = counts.get(name, 0) + 1
    return counts


def guess_ligand_resname(mol_pred: Path, het_counts: dict[str, int]) -> str | None:
    """从预测姿势文件的分子名里猜目标配体的残基名（SDF 的 _Name 常就是残基名，如 TQ3）。"""
    try:
        first = mol_pred.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    candidate = first.split()[0].upper() if first else ""
    if candidate and candidate in het_counts and candidate not in NON_LIGAND_HET:
        return candidate
    return None


def strip_ligands_from_pdb(pdb_path: Path, resnames: list[str], out_path: Path) -> int:
    """把指定残基名的 HETATM（及其 ANISOU）从 PDB 中删掉，返回删掉的原子数。"""
    targets = {r.strip().upper() for r in resnames if r.strip()}
    removed = 0
    with pdb_path.open(encoding="utf-8", errors="replace") as src, \
         out_path.open("w", encoding="utf-8") as dst:
        for line in src:
            if line.startswith(("HETATM", "ANISOU")) and line[17:20].strip().upper() in targets:
                if line.startswith("HETATM"):
                    removed += 1
                continue
            dst.write(line)
    return removed


def run_bust(mol_pred: Path, mol_true: Path | None, mol_cond: Path | None,
             out_csv: Path, full_report: bool, *, config: Path,
             top_n: int | None, outfmt: str = "csv") -> None:
    """调用 PoseBusters 的 bust 命令，结果写成 CSV。"""
    cmd = ["bust", str(mol_pred)]
    if mol_true is not None:
        cmd += ["-l", str(mol_true)]
    if mol_cond is not None:
        cmd += ["-p", str(mol_cond)]
    cmd += ["--outfmt", outfmt, "--config", str(config)]
    if top_n is not None:
        cmd += ["--top-n", str(top_n)]
    if full_report and outfmt != "short":
        cmd += ["--full-report"]
    log("运行：" + " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"PoseBusters 运行失败（退出码 {proc.returncode}）。上面是它的输出。")
    if not proc.stdout.strip():
        sys.stderr.write(proc.stderr)
        raise SystemExit("PoseBusters 没有产生任何结果。请检查输入与验证模式。")
    out_csv.write_text(proc.stdout, encoding="utf-8")
    if proc.stderr.strip():
        log("PoseBusters 提示：\n" + proc.stderr.strip())


def as_bool(value: str) -> bool | None:
    v = (value or "").strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None  # 该模式下未执行这项检查


def summarize(rows: list[dict], mode: str, expected: set[str] | None = None) -> tuple[list[dict], list[str]]:
    """把明细表压成每个姿势一行；同时返回本次实际执行了哪些检查项。"""
    if not rows:
        raise SystemExit("结果表是空的。")
    # 完整明细还包含数值和中间布尔结果，仅汇总预设的正式检查项。
    check_cols = [c for c in rows[0] if c in (CHECKS if expected is None else expected)]
    # 本次实际跑了的检查项：至少有一行给出了 True/False
    active = [c for c in check_cols
              if any(as_bool(r.get(c, "")) is not None for r in rows)]

    summary = []
    for idx, row in enumerate(rows, start=1):
        states = {c: as_bool(row.get(c, "")) for c in check_cols}
        passed = sum(value is True for value in states.values())
        failed = [c for c, value in states.items() if value is False]
        unknown = [c for c, value in states.items() if value is None]
        status = "否" if failed else ("未评估" if unknown or not passed else "是")
        summary.append({
            "序号": idx,
            "文件": row.get("file", ""),
            "分子": row.get("molecule", ""),
            "构象位置": row.get("position", ""),
            "检查项总数": len(check_cols),
            "通过项数": passed,
            "未通过项数": len(failed),
            "未评估项数": len(unknown),
            "PB_valid": status,
            "未评估项": "；".join(CHECKS.get(c, (c,))[0] for c in unknown),
            "未通过项": "；".join(CHECKS.get(c, (c,))[0] for c in failed),
            "未通过项_原始名": ";".join(failed),
        })
    return summary, active


def write_report(out_dir: Path, rows: list[dict], summary: list[dict],
                 active: list[str], mode: str,
                 mol_pred: Path, mol_true: Path | None, mol_cond: Path | None,
                 stripped_note: str = "") -> None:
    """写中文报告。"""
    total = len(summary)
    valid = sum(1 for s in summary if s["PB_valid"] == "是")
    failed = sum(s["PB_valid"] == "否" for s in summary)
    incomplete = total - valid - failed
    lines: list[str] = []
    a = lines.append

    a("# PoseBusters 对接姿势质量检查报告\n")
    a(f"- 检查模式：**{MODE_DESC.get(mode, mode)}**")
    a(f"- 预测姿势文件：`{mol_pred.name}`")
    if mol_cond is not None:
        a(f"- 蛋白结构：`{mol_cond.name}`")
        if stripped_note:
            a(f"- 预处理：{stripped_note}")
    if mol_true is not None:
        a(f"- 晶体参考配体：`{mol_true.name}`")
    a(f"- 本次执行检查项：**{len(active)} 项**")
    a(f"- 姿势数：**{total}**，通过：**{valid}**，未通过：**{failed}**，"
      f"未评估完整：**{incomplete}**")
    if total:
        a(f"- PB-valid 比例：**{valid / total * 100:.1f}%**\n")

    a("## 结论\n")
    a("通过表示当前模式中列出的检查均已通过。未评估的检查可能缺少输入，"
      "也可能因前置检查失败而未执行。\n")

    # 问题汇总：哪一项最常失败
    fail_count: dict[str, int] = {}
    for s in summary:
        for c in (s["未通过项_原始名"].split(";") if s["未通过项_原始名"] else []):
            fail_count[c] = fail_count.get(c, 0) + 1
    if fail_count:
        a("## 问题汇总（按出现次数）\n")
        a("| 检查项 | 失败姿势数 | 分组 | 说明与处理建议 |")
        a("| --- | --- | --- | --- |")
        for c, n in sorted(fail_count.items(), key=lambda kv: -kv[1]):
            zh, group, advice = CHECKS.get(c, (c, "其他", ""))
            a(f"| {zh} | {n} / {total} | {group} | {advice} |")
        a("")

    # 逐个姿势
    a("## 逐个姿势\n")
    a("| 序号 | 分子 | 构象位置 | 结果 | 通过 / 总数 | 未通过项 | 未评估项 |")
    a("| --- | --- | --- | --- | --- | --- | --- |")
    for s in summary:
        mark = {"是": "通过", "否": "未通过", "未评估": "未评估完整"}[s["PB_valid"]]
        a(f"| {s['序号']} | {s['分子']} | {s['构象位置']} | {mark} | "
          f"{s['通过项数']} / {s['检查项总数']} | {s['未通过项'] or '—'} | {s['未评估项'] or '—'} |")
    a("")

    # 本次执行了哪些检查项
    a("## 本次执行的检查项\n")
    for group in GROUP_ORDER:
        in_group = [c for c in active if CHECKS.get(c, ("", "其他", ""))[1] == group]
        if not in_group:
            continue
        a(f"**{group}**\n")
        for c in in_group:
            a(f"- {CHECKS[c][0]}（`{c}`）")
        a("")

    skipped = [c for c in CHECKS if c not in active]
    if skipped:
        a("## 本次未执行的检查项\n")
        a("以下检查项需要更多输入才能执行"
          "（给蛋白结构可启用口袋相容性检查，再给晶体参考配体可启用一致性与 RMSD 检查）：\n")
        for c in skipped:
            a(f"- {CHECKS[c][0]}（`{c}`）")
        a("")

    a("## 注意事项\n")
    a("- PoseBusters 判断的是姿势**合不合理**，不预测结合强度（Kd / ΔG），"
      "也不替代打分函数排序。")
    a("- 「与结晶水无碰撞 / 体积重叠」这两项：如果对接时本就应该置换掉该水分子，"
      "失败是预期之内的，可结合实际判断。")
    a("- RMSD ≤ 2 Å 只在提供了晶体参考配体时有意义；没有参考结构时，"
      "通过全部检查只说明姿势合理，不等于姿势正确。")
    a("- 本 App 不调用任何第三方 API，不含密钥。\n")

    a("## 引用\n")
    a("- [PoseBusters 开源仓库](https://github.com/maabuu/posebusters)")
    a("- PoseBusters 许可：MIT。")

    (out_dir / "report_zh.md").write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_posebusters.py",
        description="PoseBusters 对接姿势质量检查：输出明细表、汇总表和中文报告。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  # 只查分子本身（mol 模式）
  python3 run_posebusters.py --mol-pred docked.sdf --out-dir ./pb-out

  # 加上蛋白，查与口袋的相容性（dock 模式）
  python3 run_posebusters.py --mol-pred docked.sdf --protein receptor.pdb --out-dir ./pb-out

  # 再加晶体配体，查一致性与 RMSD（redock 模式）
  python3 run_posebusters.py --mol-pred docked.sdf --protein receptor.pdb \\
      --mol-true crystal_ligand.sdf --out-dir ./pb-out

  # 蛋白用 PDB 编号自动下载
  python3 run_posebusters.py --mol-pred docked.sdf --pdb-id 1IA1 --out-dir ./pb-out
""")
    p.add_argument("--mol-pred", required=True,
                   help="待检查的配体姿势文件（SDF/MOL/MOL2/PDB），可含多个分子或多个构象")
    p.add_argument("--protein", default=None,
                   help="蛋白结构文件（PDB），应已去掉要对接的那个配体；给了就启用 dock 模式")
    p.add_argument("--pdb-id", default=None,
                   help="或给 4 位 PDB 编号，从 RCSB 下载蛋白（与 --protein 二选一）")
    p.add_argument("--strip-ligand", default=None,
                   help="从蛋白结构里删掉这些残基名的配体（逗号分隔，如 TQ3）。"
                        "用 --pdb-id 时若不填，会尝试从姿势文件的分子名自动推断")
    p.add_argument("--no-auto-strip", action="store_true",
                   help="关掉自动推断与剥离，原样使用下载到的 PDB（一般不要用）")
    p.add_argument("--mol-true", default=None,
                   help="晶体参考配体（SDF）；给了就启用 redock 模式，增加一致性与 RMSD ≤ 2 Å 检查")
    p.add_argument("--out-dir", default="./posebusters-output", help="输出目录")
    p.add_argument("--validation-mode", default="auto", choices=sorted(PRESETS | {"auto", "custom"}))
    p.add_argument("--config-json", type=Path, help="完整的 PoseBusters JSON 配置，仅用于 custom")
    p.add_argument("--top-n", type=int, help="只检查每个预测文件的前 N 个姿势")
    p.add_argument("--output-format", choices=sorted(FORMATS), default="csv")
    p.add_argument("--full-report", action="store_true",
                   help="在明细表里附上每项检查的具体数值，而不只是通过/未通过")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top_n is not None and args.top_n < 1:
        raise SystemExit("Top N 必须为正整数。")
    if (args.validation_mode == "custom") != (args.config_json is not None):
        raise SystemExit("自定义模式需要完整 JSON 配置文件，其他模式不使用该文件。")

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "posebusters_raw"
    raw_dir.mkdir(exist_ok=True)

    mol_pred = Path(args.mol_pred).expanduser().resolve()
    if not mol_pred.is_file():
        raise SystemExit(f"找不到预测姿势文件：{mol_pred}")

    # 蛋白：文件优先于 PDB 编号
    mol_cond: Path | None = None
    if args.protein:
        mol_cond = Path(args.protein).expanduser().resolve()
        if not mol_cond.is_file():
            raise SystemExit(f"找不到蛋白结构文件：{mol_cond}")
        if args.pdb_id:
            log("同时给了 --protein 和 --pdb-id，用 --protein，忽略 --pdb-id。")
    elif args.pdb_id:
        mol_cond = fetch_pdb(args.pdb_id, raw_dir)

    # 剥离目标配体：蛋白文件里若还留着要对接的那个配体，它会和自己碰撞，结果全错。
    stripped_note = ""
    if mol_cond is not None and mol_cond.suffix.lower() == ".pdb" and not args.no_auto_strip:
        het_counts = list_het_residues(mol_cond)
        if args.strip_ligand:
            targets = [x for x in args.strip_ligand.split(",") if x.strip()]
        else:
            guessed = guess_ligand_resname(mol_pred, het_counts)
            targets = [guessed] if guessed else []
            if guessed:
                log(f"从姿势文件名推断出目标配体残基名：{guessed}")

        if targets:
            stripped_pdb = raw_dir / f"{mol_cond.stem}_ligand_removed.pdb"
            n = strip_ligands_from_pdb(mol_cond, targets, stripped_pdb)
            if n:
                log(f"已从蛋白结构里删掉 {', '.join(targets)} 共 {n} 个原子"
                    f"（保留水和辅因子，供碰撞检查用）")
                stripped_note = f"已从蛋白结构中移除目标配体 {', '.join(targets)}（{n} 个原子）"
                mol_cond = stripped_pdb
            else:
                log(f"蛋白结构里没有 {', '.join(targets)}，不用删。")
        else:
            organic = {k: v for k, v in het_counts.items() if k not in NON_LIGAND_HET}
            if organic:
                listing = "、".join(f"{k}({v} 原子)" for k, v in
                                   sorted(organic.items(), key=lambda kv: -kv[1]))
                log(f"注意：蛋白结构里还有这些有机 HETATM：{listing}。")
                log("      如果其中某个就是你要对接的配体，请用 --strip-ligand 指定它的残基名，"
                    "否则配体会和它自己碰撞，结果不可信。")

    mol_true: Path | None = None
    if args.mol_true:
        mol_true = Path(args.mol_true).expanduser().resolve()
        if not mol_true.is_file():
            raise SystemExit(f"找不到晶体参考配体文件：{mol_true}")

    if mol_true is not None:
        mode = "redock" if mol_cond is not None else "reference_only"
    else:
        mode = "dock" if mol_cond is not None else "mol"
    native_mode = ("regen" if mode == "reference_only" else mode) if args.validation_mode == "auto" else args.validation_mode
    mode_label = mode if args.validation_mode == "auto" else native_mode
    preset = native_mode.removesuffix("_fast")
    if preset in {"dock", "redock", "gen"} and mol_cond is None:
        raise SystemExit(f"{native_mode} 模式需要受体文件或 PDB 编号。")
    if preset in {"regen", "redock", "gen"} and mol_true is None:
        raise SystemExit(f"{native_mode} 模式需要参考配体。")
    if native_mode == "custom":
        config = json.loads(args.config_json.read_text(encoding="utf-8-sig"))
        if not isinstance(config, dict) or not isinstance(config.get("modules"), list) or not config["modules"]:
            raise SystemExit("JSON 配置需要一个非空的 modules 列表。")
    else:
        from yaml import safe_load

        config = safe_load(files("posebusters").joinpath(f"config/{native_mode}.yml").read_text())
    config_path = raw_dir / "resolved_config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    # Native CLI overrides top_n only when a non-None argument is provided.
    top_n = None if native_mode == "custom" and "top_n" in config else args.top_n
    names = [
        module.get("rename_outputs", {}).get(name, name + module.get("rename_suffix", ""))
        .lower().replace(" ", "_")
        for module in config["modules"]
        for name in module.get("chosen_binary_test_output", [])
    ]
    if len(set(names)) != len(names) or set(names) & {"file", "molecule", "position"}:
        raise SystemExit("正式检查列的名称必须唯一，且不得与姿势标识列重复。")
    expected = set(names)
    log(f"检查模式：{MODE_DESC.get(mode_label, mode_label)}")

    detail_csv = raw_dir / "posebusters_raw.csv"
    run_bust(mol_pred, mol_true, mol_cond, detail_csv, args.full_report, config=config_path, top_n=top_n)
    if args.output_format != "csv":
        run_bust(mol_pred, mol_true, mol_cond, out_dir / f"native_{args.output_format}.txt",
                 args.full_report, config=config_path, top_n=top_n, outfmt=args.output_format)
    from importlib.metadata import version

    (out_dir / "run_metadata.json").write_text(json.dumps({
        "posebusters": version("posebusters"), "rdkit": version("rdkit"),
        "validation_mode": native_mode, "output_format": args.output_format,
        "full_report": args.full_report, "top_n": config.get("top_n") if top_n is None else top_n,
        "receptor_preprocessing": stripped_note,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = list(csv.DictReader(detail_csv.open(encoding="utf-8")))
    summary, active = summarize(rows, mode_label, expected)

    # 明细表（原样留一份在 out_dir，方便直接下载）
    shutil.copy(detail_csv, out_dir / "results.csv")

    # 汇总表
    summary_path = out_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    write_report(out_dir, rows, summary, active, mode_label, mol_pred, mol_true, mol_cond,
                 stripped_note)

    total = len(summary)
    valid = sum(1 for s in summary if s["PB_valid"] == "是")
    log("")
    log(f"完成：{total} 个姿势，{valid} 个通过全部 {len(active)} 项检查"
        f"（PB-valid {valid / total * 100:.1f}%）" if total else "完成：没有姿势")
    log(f"输出目录：{out_dir}")
    log("  results.csv        每个姿势每项检查的明细")
    log("  summary.csv        每个姿势一行的汇总")
    log("  report_zh.md       中文报告")
    log("  posebusters_raw/   PoseBusters 原始输出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
