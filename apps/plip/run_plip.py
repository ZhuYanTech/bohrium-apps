#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_plip.py — PLIP 蛋白-配体相互作用分析的命令行封装

用途：给玻尔（Bohrium）App / 本地使用。只调用本地 PLIP，不调用任何
第三方 API，不使用任何密钥。

输入（二选一）：
  --pdb-file PATH   本地 PDB 文件
  --pdb-id 1VSN     PDB 编号（从 RCSB 下载，见 --no-download 说明）

输出（--out-dir，默认 ./plip-output）：
  interactions.csv  相互作用清单（每行一个相互作用，中英双语类型）
  report_zh.md      中文解读报告（按类型计数、关键残基、文件清单、引用）
  plip_raw/         PLIP 原始输出（*_report.xml、*_report.txt）
  images/           如有 PNG 图片则复制到此（默认不生成，因需 PyMOL）

PLIP 原生命令（供参考）：
  plip -f input.pdb -o out -xtv --model 1
  -x 生成 XML（供程序解析），-t 生成 TXT（供人阅读），-v 详细日志。
  注意：-y（PyMOL 会话）/-p（渲染图）需要 PyMOL，本镜像默认不装，
  因此封装默认不传 -y/-p；如需 3D 图，请用 PyMOL 或 Mol* 打开原 PDB。

退出码：
  0  成功（含“未检测到相互作用”——此时 CSV 只有表头，报告会明说）
  2  输入错误（文件不存在、不是 PDB、PDB ID 格式不对、下载失败等）
  3  PLIP 未安装或运行失败
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# 相互作用类型：PLIP XML 里的复数标签 -> 中文名
TYPE_ZH = {
    "hydrophobic_interactions": "疏水相互作用",
    "hydrogen_bonds": "氢键",
    "water_bridges": "水桥",
    "salt_bridges": "盐桥",
    "pi_stacks": "π-堆积",
    "pi_cation_interactions": "π-阳离子相互作用",
    "halogen_bonds": "卤键",
    "metal_complexes": "金属配位",
}

PDB_ID_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")

# 常见结晶溶剂 / 添加剂的 HETATM 三字母代码（PLIP 会把它们都当配体算）。
# 报告默认不丢弃它们，只按配体分开计数；--exclude-solvents 才会过滤掉。
COMMON_SOLVENTS = {
    "DMS", "EDO", "GOL", "SO4", "PO4", "ACT", "ACE", "TRS", "MES",
    "PEG", "PG4", "PGE", "MPD", "BME", "CIT", "TAR", "NO3", "CL",
    "NA", "K", "CA", "MG", "ZN", "FE", "HOH", "WAT", "IOD", "BR",
}


def fail(message: str, code: int = 2) -> "SystemExit":
    print(f"错误：{message}", file=sys.stderr)
    return SystemExit(code)


def download_pdb(pdb_id: str, dest: Path) -> Path:
    """从 RCSB 下载 PDB 文件。失败时给出中文提示，不静默造数据。"""
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    print(f"正在从 RCSB 下载 {pdb_id.upper()}：{url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "plip-bohrium-app/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:  # noqa: BLE001 - 要把原因原样告诉用户
        raise RuntimeError(f"下载 PDB {pdb_id} 失败（{url}）：{exc}。请检查网络，"
                           "或改用 --pdb-file 传入本地 PDB 文件。") from exc
    return dest


def validate_pdb(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"PDB 文件不存在：{path}")
    if path.stat().st_size == 0:
        raise ValueError(f"PDB 文件为空：{path}")
    text = path.read_text(errors="ignore")
    if not re.search(r"^(ATOM|HETATM)\s", text, re.MULTILINE):
        raise ValueError(f"文件里没有 ATOM / HETATM 记录，不像是 PDB 文件：{path}")
    if "HETATM" not in text:
        print("提示：文件中没有 HETATM 记录，可能没有配体，PLIP 可能检测不到相互作用。")


def run_plip(plip_cmd: str, pdb_path: Path, raw_dir: Path, model: int) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    cmd = [plip_cmd, "-f", str(pdb_path), "-o", str(raw_dir),
           "-x", "-t", "-v", "--model", str(model)]
    print("运行命令：" + " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"找不到 PLIP 可执行文件 '{plip_cmd}'。请先安装：pip install plip==3.0.1，"
            "或使用本仓库的 Dockerfile 构建镜像。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("PLIP 运行超时（600 秒）。该结构可能过大，请换更小的结构或分模型提交。") from exc
    print(proc.stdout[-2000:] if proc.stdout else "")
    if proc.stderr:
        print(proc.stderr[-2000:], file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"PLIP 运行失败，退出码 {proc.returncode}。请看上方日志；"
                           "常见原因是 PDB 格式损坏或缺少 OpenBabel 依赖。")


def _text(elem: ET.Element | None) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def parse_xml(xml_path: Path) -> tuple[list[dict], dict]:
    """解析一份 PLIP XML，返回（相互作用行，元信息）。"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    version = _text(root.find("plipversion"))
    rows: list[dict] = []
    meta: dict = {"plip_version": version, "pdbid": _text(root.find("pdbid")),
                  "model": _text(root.find("model")), "ligands": []}
    for site in root.iter("bindingsite"):
        ident = site.find("identifiers")
        ligand = _text(ident.find("longname")) if ident is not None else ""
        ligtype = _text(ident.find("ligtype")) if ident is not None else ""
        hetid = _text(ident.find("hetid")) if ident is not None else ""
        chain = _text(ident.find("chain")) if ident is not None else ""
        position = _text(ident.find("position")) if ident is not None else ""
        if ligand:
            meta["ligands"].append(
                {"ligand": ligand, "hetid": hetid, "chain": chain,
                 "position": position, "type": ligtype})
        interactions = site.find("interactions")
        if interactions is None:
            continue
        for group in interactions:
            type_en = group.tag  # 如 hydrogen_bonds
            for item in group:
                fields = {child.tag: _text(child) for child in item}
                dist = (fields.get("dist") or fields.get("dist_h-a")
                        or fields.get("dist_d-a") or "")
                # 其余字段原样保留在 details 里，不丢信息
                details = {k: v for k, v in fields.items()
                           if k not in ("resnr", "restype", "reschain", "dist",
                                        "dist_h-a", "dist_d-a")}
                rows.append({
                    "binding_site": site.get("id", ""),
                    "ligand": ligand,
                    "ligand_chain": chain,
                    "ligand_resnr": position,
                    "interaction_type_en": type_en,
                    "interaction_type_zh": TYPE_ZH.get(type_en, type_en),
                    "resnr": fields.get("resnr", ""),
                    "restype": fields.get("restype", ""),
                    "reschain": fields.get("reschain", ""),
                    "distance_angstrom": dist,
                    "details": json.dumps(details, ensure_ascii=False),
                })
    return rows, meta


def write_csv(rows: list[dict], path: Path) -> None:
    columns = ["binding_site", "ligand", "ligand_chain", "ligand_resnr",
               "interaction_type_en", "interaction_type_zh",
               "resnr", "restype", "reschain", "distance_angstrom", "details"]
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict], meta: dict, out_dir: Path,
                 source_desc: str, raw_files: list[str],
                 filter_note: str = "") -> Path:
    counts = Counter(r["interaction_type_zh"] for r in rows)
    per_ligand = Counter(r["ligand"] for r in rows if r["ligand"])
    solvent_rows = sum(n for lig, n in per_ligand.items() if lig in COMMON_SOLVENTS)
    residues = Counter(f'{r["restype"]}{r["resnr"]}（{r["reschain"]}链）'
                       for r in rows if r["resnr"])
    ligand_desc = ", ".join(
        f"{l['ligand']}（{l['chain']}链，残基 {l['position']}，{l['type']}）"
        for l in meta["ligands"]) or "无"
    lines = [
        "# PLIP 蛋白-配体相互作用分析报告",
        "",
        f"- 输入：{source_desc}",
        f"- PLIP 版本：{meta.get('plip_version') or '未知'}（XML 中记录）",
        f"- 模型：{meta.get('model') or '—'}",
        f"- 检测到的配体：{ligand_desc}",
        f"- 相互作用总数：{len(rows)}",
        f"- 按配体分开：{'; '.join(f'{lig} {n} 个' for lig, n in per_ligand.most_common()) or '无'}",
        *( [f"- 过滤说明：{filter_note}"] if filter_note else []),
        "",
        "## 按类型统计",
        "",
    ]
    if counts:
        lines.append("| 相互作用类型 | 数量 |")
        lines.append("| --- | ---: |")
        for name, num in counts.most_common():
            lines.append(f"| {name} | {num} |")
    else:
        lines.append("未检测到相互作用。可能原因：结构中没有配体、配体不在结合口袋、"
                     "或 PDB 模型/链选择不对。请检查输入文件。")
    # 按配体分开计数：3MXF 的教训——总数 27 里 JQ1 只有 14 个，
    # 其余是结晶溶剂 DMS/EDO。只看总数会误以为都是目标配体的。
    lines += ["", "## 按配体统计（不要只看总数）", ""]
    if per_ligand:
        lines.append("| 配体 | 数量 | 备注 |")
        lines.append("| --- | ---: | --- |")
        for lig, num in per_ligand.most_common():
            note = "常见结晶溶剂/添加剂，不是目标配体" if lig in COMMON_SOLVENTS else "目标配体"
            lines.append(f"| {lig} | {num} | {note} |")
        if solvent_rows and len(per_ligand) > 1:
            lines.append("")
            lines.append(f"注意：总数 {len(rows)} 个里有 {solvent_rows} 个来自结晶溶剂，"
                         "评价结合模式时请看目标配体那一行；"
                         "只想看目标配体时可用 `--ligand <配体名>` 或 `--exclude-solvents` 重新跑。")
    else:
        lines.append("未检测到配体。")
    lines += ["", "## 关键残基（按相互作用次数排序）", ""]
    if residues:
        lines.append("| 残基 | 相互作用数 |")
        lines.append("| --- | ---: |")
        for res, num in residues.most_common(10):
            lines.append(f"| {res} | {num} |")
        top = residues.most_common(3)
        lines.append("")
        lines.append("解读提示：排在前面的残基通常是结合的关键锚点；"
                     f"例如 {top[0][0]} 参与了 {top[0][1]} 个相互作用，"
                     "突变或修饰它时要格外小心。")
    else:
        lines.append("无。")
    lines += [
        "",
        "## 输出文件",
        "",
        "- `interactions.csv`：每行一个相互作用，可直接用 Excel / pandas 打开。",
        "- `plip_raw/`：PLIP 原始 XML / TXT 报告。",
        "- `images/`：如有 PNG 图片会在此（默认不生成，见 README 说明）。",
        "",
        "## 注意事项",
        "",
        "- PLIP 只检测“有什么相互作用”，不预测结合亲和力（Kd / ΔG），"
        "不要把相互作用个数直接当成亲和力高低。",
        "- 距离、角度阈值用的是 PLIP 默认值；如需调整，请在玻尔 App 的高级参数里说明。",
        "",
        "## 引用",
        "",
        "- Salentin, S. et al. PLIP: fully automated protein-ligand interaction profiler. "
        "Nucleic Acids Res. 43 (W1), W443–W447 (2015). doi:10.1093/nar/gkv315",
        "- Schake, P., Bolz, S. N. et al. PLIP 2025: introducing protein–protein interactions "
        "to the protein–ligand interaction profiler. Nucleic Acids Res. (2025), gkaf361. "
        "doi:10.1093/nar/gkaf361",
        "- PLIP 许可：GNU GPLv2；代码与 Docker 镜像：github.com/pharmai/plip，"
        "Docker Hub：pharmai/plip。",
        "",
    ]
    path = out_dir / "report_zh.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PLIP 蛋白-配体相互作用分析（玻尔 App 封装）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdb-file", type=Path, help="本地 PDB 文件路径")
    group.add_argument("--pdb-id", help="PDB 编号，如 1VSN（自动从 RCSB 下载）")
    parser.add_argument("--out-dir", type=Path, default=Path("./plip-output"),
                        help="输出目录（默认 ./plip-output）")
    parser.add_argument("--model", type=int, default=1, help="PDB 模型编号（默认 1）")
    parser.add_argument("--ligand", help="只分析指定配体，如 --ligand JQ1（默认分析全部配体）")
    parser.add_argument("--exclude-solvents", action="store_true",
                        help="过滤 DMS、EDO 等常见结晶溶剂/添加剂，只保留目标配体")
    parser.add_argument("--plip-cmd", default="plip", help="PLIP 可执行文件名（默认 plip）")
    args = parser.parse_args(argv)

    try:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        if args.pdb_id:
            pdb_id = args.pdb_id.strip().upper()
            if not PDB_ID_RE.match(pdb_id):
                print(f"错误：PDB ID 格式不对：{args.pdb_id}（应为 4 位，如 1VSN）。",
                      file=sys.stderr)
                return 2
            pdb_path = args.out_dir / f"{pdb_id}.pdb"
            download_pdb(pdb_id, pdb_path)
            source_desc = f"PDB ID {pdb_id}（从 RCSB 下载）"
        else:
            pdb_path = args.pdb_file
            source_desc = f"本地文件 {pdb_path}"
        validate_pdb(pdb_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    raw_dir = args.out_dir / "plip_raw"
    try:
        run_plip(args.plip_cmd, pdb_path, raw_dir, args.model)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    xml_files = sorted(raw_dir.glob("*_report.xml"))
    txt_files = sorted(raw_dir.glob("*_report.txt"))
    if not xml_files and not txt_files:
        print("错误：PLIP 运行后没有生成报告文件（plip_raw 目录为空）。", file=sys.stderr)
        print("提示：这通常表示结构中没有可分析的配体，或 PLIP 版本与封装不匹配。", file=sys.stderr)
        return 3

    all_rows: list[dict] = []
    meta: dict = {"plip_version": "", "pdbid": "", "model": str(args.model), "ligands": []}
    for xml_path in xml_files:
        try:
            rows, m = parse_xml(xml_path)
        except ET.ParseError as exc:
            print(f"警告：解析 {xml_path.name} 失败：{exc}，已跳过该文件。", file=sys.stderr)
            continue
        all_rows.extend(rows)
        if m.get("plip_version"):
            meta["plip_version"] = m["plip_version"]
        meta["ligands"].extend(m["ligands"])

    # 配体过滤（在解析之后、写 CSV/报告之前；原始 XML/TXT 仍保留全部配体）
    filter_note = ""
    if args.ligand:
        wanted = args.ligand.strip().upper()
        kept = [r for r in all_rows if r["ligand"].upper() == wanted]
        if not kept:
            print(f"错误：未找到配体 {wanted}。本结构检测到的配体："
                  + ", ".join(sorted({r['ligand'] for r in all_rows if r['ligand']})) + "。", file=sys.stderr)
            return 2
        filter_note = f"只保留配体 {wanted}（共 {len(all_rows)} 个里保留 {len(kept)} 个）"
        all_rows = kept
    elif args.exclude_solvents:
        kept = [r for r in all_rows if r["ligand"] not in COMMON_SOLVENTS]
        removed = sorted({r["ligand"] for r in all_rows if r["ligand"] in COMMON_SOLVENTS})
        filter_note = (f"已过滤结晶溶剂 {', '.join(removed)}"
                       f"（共 {len(all_rows)} 个里保留 {len(kept)} 个）" if removed
                       else "未检测到常见结晶溶剂，无需过滤")
        all_rows = kept
    write_csv(all_rows, args.out_dir / "interactions.csv")
    report = write_report(all_rows, meta, args.out_dir, source_desc,
                          [p.name for p in xml_files + txt_files],
                          filter_note=filter_note)

    # PNG 图片：PLIP 默认不生成（需 PyMOL），有则复制，没有也不报错
    images_dir = args.out_dir / "images"
    pngs = list(raw_dir.glob("*.png"))
    if pngs:
        images_dir.mkdir(exist_ok=True)
        for png in pngs:
            shutil.copy2(png, images_dir / png.name)

    counts = Counter(r["interaction_type_zh"] for r in all_rows)
    per_ligand = Counter(r["ligand"] for r in all_rows if r["ligand"])
    print(f"完成：共 {len(all_rows)} 个相互作用，"
          + ("；".join(f"{k} {v}" for k, v in counts.most_common()) if counts else "未检测到相互作用"))
    if per_ligand:
        print("按配体：" + "；".join(f"{lig} {n} 个" for lig, n in per_ligand.most_common()))
    if filter_note:
        print(filter_note)
    print(f"输出目录：{args.out_dir.resolve()}")
    print(f"  - interactions.csv\n  - {report.name}\n  - plip_raw/（原始 XML / TXT）")
    if not all_rows:
        print("提示：未检测到相互作用，详见 report_zh.md 的说明。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
