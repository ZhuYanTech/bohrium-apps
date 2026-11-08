#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_openfold3.py — OpenFold3 结构预测的命令行封装

用途：给玻尔（Bohrium）App / 本地使用。把输入转成 OpenFold3 的
query.json + runner.yml，调用本地 `run_openfold predict`，再把各样本的
置信度汇总成 CSV 与中文报告。

输入（单条蛋白链；配体、DNA、RNA 各可选一条）：
  蛋白（三选一，必选其一）：
    --protein-sequence SEQ | --protein-sequence-file FILE   粘贴序列或 FASTA
    --pdb-id ID                                             4 位编号，从 RCSB 取第一条链
    --pdb-file FILE                                         PDB 文件，提取第一条链的序列
  配体（可选，三选一，至多一种）：
    --ligand-smiles SMILES | --ligand-sdf-file FILE | --ligand-pubchem-cid CID
  --dna-sequence SEQ        DNA 序列（可选，A/T/G/C）
  --rna-sequence SEQ        RNA 序列（可选，A/U/G/C）
  --modifications "3:SEP,5:MHO"   残基修饰（位置:修饰代码，逗号分隔）
  --pocket "B|A:45,A:46|4.0"      口袋约束（配体链|蛋白链:残基,…|最大距离 Å）
  --msa-file FILE           自备 .a3m MSA（指定后跳过自动生成）
  --no-msa                  显式不用 MSA（单序列模式，精度可能下降）
  --no-templates            不用结构模板
  --model-seeds N           模型种子数（默认 1，范围 1–5）
  --diffusion-samples N     每种子扩散样本数（默认 5，范围 1–10）
  --random-seed N           固定随机种子（留空则每次随机）
  --output-format cif|pdb   输出结构格式（默认 cif）

输出（--out-dir，默认 ./openfold3-output）：
  query.json            生成的 OpenFold3 输入（可复核、可直接拿去跑 run_openfold）
  runner.yml            生成的配置（输出格式、随机种子、口袋采样开关）
  summary.csv           各样本置信度汇总（按 sample_ranking_score 排序）
  predicted.cif/.pdb    排名第一的预测结构
  report_zh.md          中文解读报告（置信度分段、pTM/ipTM 解读、注意事项）
  openfold3_raw/        OpenFold3 原生输出（各样本结构、置信度 JSON、MSA、timing）

OpenFold3 原生命令（供参考）：
  run_openfold predict --query-json query.json \
      --inference-ckpt-path /opt/openfold3-cache/of3-ob-2025-06-30-174k.pt \
      --use-msa-server=True --use-templates=True \
      --num-model-seeds 1 --num-diffusion-samples 5 \
      --runner-yaml runner.yml --output-dir OUT

退出码：
  0  成功（结构 + 置信度齐全）
  2  输入错误（序列非法、SMILES 非法、口袋约束非法、MSA 不匹配等）
  3  run_openfold 未安装或运行失败（含静默显存不足：退出码为 0 但无输出文件）

OpenFold3 版本：只用 v0.5.0（Apache 2.0，代码与权重均可商用），检查点
OpenBind-0 of3-ob-2025-06-30-174k.pt（约 2.29 GB），构建时烤进镜像，
运行时用 --inference-ckpt-path 显式指定，不依赖默认检查点名。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OF3_VERSION = "0.5.0"
CKPT_NAME = "of3-ob-2025-06-30-174k.pt"
CKPT_SIZE = 2287872989
DEFAULT_CKPT_PATH = "/opt/openfold3-cache/of3-ob-2025-06-30-174k.pt"
DEFAULT_MSA_SERVER_URL = "https://api.colabfold.com"
QUERY_KEY = "query_1"

PROTEIN_CHAIN = "A"
LIGAND_CHAIN = "B"
DNA_CHAIN = "C"
RNA_CHAIN = "D"

MAX_RESIDUES = 1600
WARN_RESIDUES = 1000

# 蛋白：20 种标准氨基酸 + X（未知）+ U（硒代半胱氨酸）。
PROTEIN_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYXU]+$")
DNA_RE = re.compile(r"^[ATGCN]+$")
RNA_RE = re.compile(r"^[AUGCN]+$")
SMILES_CHAR_RE = re.compile(r"^[A-Za-z0-9\[\]()=#+\-/\\@%.*~$]+$")
PDB_ID_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")
CCD_RE = re.compile(r"^[A-Z0-9]{2,4}$")

# 3 字母残基名 → 1 字母（含硒代甲硫氨酸/硒代半胱氨酸）。
RES3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M", "SEC": "U", "PYL": "K", "ASX": "B", "GLX": "Z",
    "XAA": "X", "UNK": "X",
}

# pLDDT 分段（与官方文档一致）。
PLDDT_BANDS = [
    (90, "很高（主链与侧链均可靠）"),
    (70, "高（主链准确）"),
    (50, "中等（谨慎对待）"),
    (0, "低（可能为无序区或不确定）"),
]


def fail(message: str, code: int = 2) -> "SystemExit":
    print(f"错误：{message}", file=sys.stderr)
    return SystemExit(code)


# ---------------------------------------------------------------- 输入处理

def clean_sequence(raw: str) -> str:
    """去掉 FASTA 头、空白与换行，转大写。"""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not ln.startswith(">")]
    return "".join(lines).replace(" ", "").replace("\t", "").upper()


def validate_protein_sequence(sequence: str) -> tuple[str, list[str]]:
    """返回（清洗后的序列，警告列表）。非法时抛 ValueError。"""
    sequence = clean_sequence(sequence)
    if not sequence:
        raise ValueError("蛋白序列为空。请粘贴氨基酸序列、输入 PDB 编号或上传 PDB 文件。")
    if len(sequence) > MAX_RESIDUES:
        raise ValueError(
            f"蛋白序列共 {len(sequence)} 个残基，超过上限 {MAX_RESIDUES}。"
            "24 GB 显存的机型装不下这么大的复合物，请换更小的结构或分段提交。")
    bad = sorted(set(sequence) - set("ACDEFGHIKLMNPQRSTVWYXU"))
    if bad:
        raise ValueError(
            f"蛋白序列含非法字符：{''.join(bad)}。只接受 20 种标准氨基酸字母"
            "（ACDEFGHIKLMNPQRSTVWY）加 X（未知）与 U（硒代半胱氨酸）。")
    if not PROTEIN_RE.match(sequence):
        raise ValueError("蛋白序列格式不对。请检查是否混入数字、空格或非氨基酸字符。")
    warnings: list[str] = []
    if len(sequence) > WARN_RESIDUES:
        warnings.append(
            f"蛋白共 {len(sequence)} 个残基，超过 {WARN_RESIDUES}，"
            "建议用 32 GB 以上显存的机型，24 GB 机型可能显存不足。")
    return sequence, warnings


def validate_nucleic_sequence(raw: str, kind: str) -> str:
    """kind 为 dna 或 rna。非法时抛 ValueError。"""
    sequence = clean_sequence(raw)
    if not sequence:
        raise ValueError(f"{kind.upper()} 序列为空。")
    pattern = DNA_RE if kind == "dna" else RNA_RE
    alphabet = "A/T/G/C（+N）" if kind == "dna" else "A/U/G/C（+N）"
    if not pattern.match(sequence):
        raise ValueError(
            f"{kind.upper()} 序列含非法字符：{sequence[:40]}。"
            f"只接受 {alphabet}。")
    return sequence


def validate_smiles(smiles: str) -> str:
    """返回清洗后的 SMILES。非法时抛 ValueError。"""
    smiles = smiles.strip()
    if not smiles:
        raise ValueError("配体 SMILES 为空。")
    if any(c.isspace() for c in smiles):
        raise ValueError("SMILES 里不能有空格。")
    if not SMILES_CHAR_RE.match(smiles):
        raise ValueError(f"SMILES 含非法字符：{smiles}")
    if smiles.count("(") != smiles.count(")"):
        raise ValueError(f"SMILES 圆括号不配对：{smiles}")
    if smiles.count("[") != smiles.count("]"):
        raise ValueError(f"SMILES 方括号未闭合：{smiles}")
    return smiles


def parse_modifications(value: str, sequence_len: int) -> dict[str, str]:
    """解析 --modifications，形如 "3:SEP,5:MHO"。"""
    result: dict[str, str] = {}
    for item in value.split(","):
        item = item.strip()
        m = re.match(r"^(\d+):([A-Za-z0-9]{2,4})$", item)
        if not m:
            raise ValueError(
                f"残基修饰格式不对：{item}（应为 位置:修饰代码，如 3:SEP，多个用逗号分隔）。")
        pos, code = int(m.group(1)), m.group(2).upper()
        if not 1 <= pos <= sequence_len:
            raise ValueError(
                f"修饰位置 {pos} 超出蛋白长度 {sequence_len}。")
        if not CCD_RE.match(code):
            raise ValueError(f"修饰代码格式不对：{code}（应为 2–4 位字母数字，如 SEP）。")
        if str(pos) in result:
            raise ValueError(f"修饰位置 {pos} 重复。")
        result[str(pos)] = code
    if not result:
        raise ValueError("残基修饰为空。")
    return result


def parse_pocket(value: str, protein_len: int) -> dict:
    """解析 --pocket，形如 "B|A:45,A:46|4.0"。

    返回 query.json 用的 pocket_constraint 字典。
    """
    parts = value.split("|")
    if len(parts) not in (2, 3):
        raise ValueError(
            f"口袋约束格式不对：{value}（应为 配体链|蛋白链:残基,…|最大距离，"
            "如 B|A:45,A:46|4.0；最大距离可省略，默认 4.0 Å）。")
    ligand_chain, residues_part = parts[0].strip().upper(), parts[1].strip()
    if ligand_chain != LIGAND_CHAIN:
        raise ValueError(
            f"口袋约束的配体链只能是 {LIGAND_CHAIN}（本任务的配体链），"
            f"不是 {ligand_chain}。")
    max_distance = 4.0
    if len(parts) == 3:
        try:
            max_distance = float(parts[2].strip())
        except ValueError as exc:
            raise ValueError(f"口袋最大距离不是数字：{parts[2]}。") from exc
        if not 0.5 <= max_distance <= 20.0:
            raise ValueError(
                f"口袋最大距离 {max_distance} 超出范围 0.5–20 Å。")
    residues: list[list] = []
    for item in residues_part.split(","):
        item = item.strip()
        m = re.match(r"^([A-Za-z]):(\d+)$", item)
        if not m:
            raise ValueError(
                f"口袋残基格式不对：{item}（应为 链:残基号，如 A:45）。")
        chain, res = m.group(1).upper(), int(m.group(2))
        if chain != PROTEIN_CHAIN:
            raise ValueError(
                f"口袋约束只支持蛋白链 {PROTEIN_CHAIN}，不支持链 {chain}。")
        if not 1 <= res <= protein_len:
            raise ValueError(
                f"口袋残基号 {res} 超出蛋白长度 {protein_len}。")
        residues.append([chain, res])
    if not residues:
        raise ValueError("口袋约束的残基列表为空。")
    return {
        "ligand_chain_id": ligand_chain,
        "pocket_residues": residues,
        "max_distance": max_distance,
    }


def fetch_pdb_fasta(pdb_id: str) -> str:
    """从 RCSB 取 PDB 编号对应的 FASTA，返回第一条链的序列。"""
    pdb_id = pdb_id.strip().upper()
    if not PDB_ID_RE.match(pdb_id):
        raise ValueError(
            f"PDB 编号格式不对：{pdb_id}（应为 4 位，如 1UBQ）。")
    url = f"https://www.rcsb.org/fasta/entry/{pdb_id}"
    print(f"从 RCSB 下载 FASTA：{url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "openfold3-app/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f"RCSB 上找不到 PDB 编号 {pdb_id}（HTTP {exc.code}）。") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(
            f"无法访问 RCSB（{exc}）。请检查节点出网，或改用粘贴序列/上传 PDB 文件。") from exc
    sequence = clean_sequence(text)
    if not sequence:
        raise ValueError(f"RCSB 返回的 {pdb_id} 没有序列。")
    return sequence


def fetch_pubchem_smiles(cid: str) -> str:
    """按 PubChem 编号取标准 SMILES。"""
    cid = cid.strip()
    if not cid.isdigit():
        raise ValueError(f"PubChem 编号格式不对：{cid}（应为纯数字，如 2244）。")
    url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
           f"{cid}/property/CanonicalSMILES/JSON")
    print(f"从 PubChem 取 SMILES：{url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "openfold3-app/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f"PubChem 上找不到编号 {cid}（HTTP {exc.code}）。") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(
            f"无法访问 PubChem（{exc}）。请检查节点出网，或改用粘贴 SMILES/上传 SDF 文件。") from exc
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"PubChem 返回的结果无法解析：{exc}。") from exc
    try:
        smiles = data["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"PubChem 编号 {cid} 没有标准 SMILES。") from exc
    return smiles


def extract_sequence_from_pdb(pdb_path: Path) -> tuple[str, str]:
    """从 PDB 文件提取第一条链的序列。

    优先用 SEQRES，没有时用 ATOM 的 CA 原子。返回（序列，来源说明）。
    """
    text = pdb_path.read_text(errors="ignore")
    seqres: dict[str, list[str]] = {}
    atom_res: dict[str, list[str]] = {}
    for line in text.splitlines():
        record = line[0:6].strip()
        if record == "SEQRES":
            chain = line[11:12].strip() or "A"
            seqres.setdefault(chain, []).extend(line[19:].split())
        elif record == "ATOM" and line[12:16].strip() == "CA":
            chain = line[21:22].strip() or "A"
            atom_res.setdefault(chain, []).append(line[17:20].strip())
    for source, mapping in (("SEQRES", seqres), ("ATOM CA", atom_res)):
        for chain in sorted(mapping):
            codes = mapping[chain]
            if not codes:
                continue
            unknown = sorted({c for c in codes if c not in RES3_TO_1})
            if unknown:
                raise ValueError(
                    f"PDB 文件 {chain} 链含无法识别的残基：{', '.join(unknown)}。")
            sequence = "".join(RES3_TO_1[c] for c in codes)
            return sequence, f"PDB 文件 {chain} 链（{source}，{len(sequence)} 个残基）"
    raise ValueError(
        f"PDB 文件里没有可提取的序列：{pdb_path}（既无 SEQRES，也无 CA 原子）。")


def sdf_to_smiles(sdf_path: Path) -> tuple[str, str]:
    """把 SDF/MOL/MOL2 文件转成 SMILES。

    先试 OpenBabel（镜像里已装），再试 RDKit；两者都没有时报运行环境错误。
    返回（SMILES，转换方式）。
    """
    obabel = shutil.which("obabel")
    if obabel is not None:
        proc = subprocess.run([obabel, str(sdf_path), "-osmi"],
                              capture_output=True, text=True, timeout=120)
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            smiles = line.split()[0]
            return validate_smiles(smiles), "OpenBabel"
        raise ValueError(
            f"OpenBabel 无法从 {sdf_path.name} 读出 SMILES："
            f"{(proc.stderr or '').strip()[-200:]}")
    try:
        from rdkit import Chem  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "SDF 转换需要 OpenBabel 或 RDKit，本机两者都没装。"
            "镜像里已装 OpenBabel，本地运行时请先装其一："
            "apt install openbabel，或 pip install rdkit。") from exc
    suppl = Chem.SDMolSupplier(str(sdf_path), removeHs=False)
    mol = next((m for m in suppl if m is not None), None)
    if mol is None:
        raise ValueError(f"RDKit 无法解析 SDF 文件：{sdf_path}")
    return validate_smiles(Chem.MolToSmiles(mol)), "RDKit"


def validate_msa_file(msa_path: Path, sequence: str) -> None:
    """检查 .a3m 文件：存在、非空、第一条序列与输入蛋白序列一致
    （忽略空位符 -/. 与大小写）。不一致时抛 ValueError。"""
    if not msa_path.exists():
        raise FileNotFoundError(f"MSA 文件不存在：{msa_path}")
    if msa_path.stat().st_size == 0:
        raise ValueError(f"MSA 文件为空：{msa_path}")
    first_seq = ""
    for line in msa_path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        first_seq = line
        break
    if not first_seq:
        raise ValueError(f"MSA 文件里没有序列：{msa_path}")
    cleaned = re.sub(r"[-.]", "", first_seq).upper()
    if cleaned != sequence:
        raise ValueError(
            "MSA 文件第一条序列与输入的蛋白序列不一致（去掉空位符后比较）。"
            "请确认 .a3m 对应的是同一条链，否则跳过 MSA 生成会算错。")


# ---------------------------------------------------------------- 输入生成

def build_query(protein_sequence: str, ligand_smiles: str | None,
                dna_sequence: str | None, rna_sequence: str | None,
                modifications: dict[str, str] | None,
                pocket: dict | None, msa_path: str | None,
                use_msas: bool) -> dict:
    """生成 OpenFold3 query.json 内容（单条查询 query_1）。"""
    protein: dict = {
        "molecule_type": "protein",
        "chain_ids": PROTEIN_CHAIN,
        "sequence": protein_sequence,
    }
    if modifications:
        protein["non_canonical_residues"] = modifications
    if msa_path is not None:
        protein["main_msa_file_paths"] = msa_path
    chains = [protein]
    if ligand_smiles is not None:
        chains.append({
            "molecule_type": "ligand",
            "chain_ids": LIGAND_CHAIN,
            "smiles": ligand_smiles,
        })
    if dna_sequence is not None:
        chains.append({
            "molecule_type": "dna",
            "chain_ids": DNA_CHAIN,
            "sequence": dna_sequence,
        })
    if rna_sequence is not None:
        chains.append({
            "molecule_type": "rna",
            "chain_ids": RNA_CHAIN,
            "sequence": rna_sequence,
        })
    query: dict = {"chains": chains, "use_msas": use_msas}
    if pocket is not None:
        query["pocket_constraint"] = pocket
    return {"queries": {QUERY_KEY: query}}


def build_runner_yaml(output_format: str, random_seed: int | None,
                      pocket_present: bool) -> str:
    """生成 runner.yml（只覆盖需要改的设置，其余用 OpenFold3 默认值）。"""
    lines = [
        "# 由 run_openfold3.py 生成；只覆盖需要改的设置，其余用 OpenFold3 默认值。",
        "output_writer_settings:",
        f"  structure_format: {output_format}",
    ]
    if random_seed is not None:
        lines += [
            "experiment_settings:",
            "  seeds:",
            f"    - {random_seed}",
        ]
    if pocket_present:
        lines += [
            "dataset_config_kwargs:",
            "  pocket_sampling:",
            "    enabled: true",
        ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 输出解析

def parse_aggregated(path: Path) -> dict:
    """解析 *_confidences_aggregated.json。缺关键字段时抛 ValueError。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"置信度 JSON 无法解析：{path}（{exc}）") from exc
    for key in ("avg_plddt", "ptm", "iptm", "sample_ranking_score", "has_clash"):
        if key not in data:
            raise ValueError(f"置信度 JSON 缺少字段 {key}：{path}")
    return data


def plddt_band(value: float) -> str:
    """pLDDT 分段说明。"""
    for threshold, desc in PLDDT_BANDS:
        if value >= threshold:
            return desc
    return PLDDT_BANDS[-1][1]


def write_summary_csv(out_dir: Path, rows: list[dict]) -> Path:
    """写 summary.csv（按 sample_ranking_score 从高到低）。"""
    path = out_dir / "summary.csv"
    fields = ["rank", "seed", "sample", "structure_file", "avg_plddt", "ptm",
              "iptm", "sample_ranking_score", "has_clash", "disorder", "gpde"]
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows, start=1):
            writer.writerow({
                "rank": i,
                "seed": row["seed"],
                "sample": row["sample"],
                "structure_file": row["structure_file"],
                "avg_plddt": f"{row['avg_plddt']:.2f}",
                "ptm": f"{row['ptm']:.4f}",
                "iptm": f"{row['iptm']:.4f}",
                "sample_ranking_score": f"{row['sample_ranking_score']:.4f}",
                "has_clash": int(row["has_clash"]),
                "disorder": (f"{row['disorder']:.4f}"
                             if row.get("disorder") is not None else ""),
                "gpde": (f"{row['gpde']:.4f}"
                         if row.get("gpde") is not None else ""),
            })
    return path


def write_report(out_dir: Path, summary: dict, rows: list[dict],
                 msa_mode: str, templates_on: bool, warnings: list[str],
                 missing_note: str = "") -> Path:
    """写中文解读报告 report_zh.md。"""
    best = rows[0] if rows else None
    lines = ["# OpenFold3 结构预测报告", ""]
    lines += [
        f"- 蛋白：{summary['protein_len']} 个残基（{PROTEIN_CHAIN} 链）"
        + (f"，来源：{summary['protein_source']}" if summary.get("protein_source") else ""),
        f"- 复合物：{summary['composition']}",
        f"- MSA：{msa_mode}",
        f"- 模板：{'开启' if templates_on else '关闭'}",
        f"- 模型：OpenFold3 v{OF3_VERSION}，检查点 OpenBind-0（Apache 2.0）",
        f"- 设置：模型种子 {summary['model_seeds']}、每种子扩散样本 "
        f"{summary['diffusion_samples']}、输出格式 {summary['output_format']}",
    ]
    if summary.get("pocket_desc"):
        lines.append(f"- 口袋约束：{summary['pocket_desc']}")
    if summary.get("random_seed") is not None:
        lines.append(f"- 随机种子：{summary['random_seed']}（固定，可复现）")
    lines.append("")
    if warnings:
        lines += ["## 提示", ""]
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines += ["## 排名第一的样本", ""]
    if best is not None:
        lines += [
            f"样本：种子 {best['seed']}，样本 {best['sample']}，"
            f"结构文件 `{best['structure_file']}`。",
            "",
            "| 指标 | 数值 | 说明 |",
            "| --- | ---: | --- |",
            f"| 平均 pLDDT | {best['avg_plddt']:.2f} | {plddt_band(best['avg_plddt'])} |",
            f"| pTM | {best['ptm']:.4f} | 整体结构准确度；单链蛋白高于 0.7 一般表示预测可信 |",
            f"| ipTM | {best['iptm']:.4f} | 界面 pTM；预测复合物时优先看高 ipTM 的样本 |",
            f"| 排序分 | {best['sample_ranking_score']:.4f} | pTM、ipTM、无序度、冲突的加权和，用于给样本排序 |",
            f"| 冲突 has_clash | {int(best['has_clash'])} | 1 表示链间存在空间冲突，0 表示无冲突 |",
        ]
        if best.get("disorder") is not None:
            lines.append(f"| 无序度 disorder | {best['disorder']:.4f} | 平均相对溶剂可及面积，高值多见于无序区 |")
        lines += [
            "",
            "解读：先看 pTM 与 ipTM，再看 pLDDT 分布；多个样本间结构一致，"
            "比单个高分更可信。pLDDT 低于 50 的区域常为天然无序区，"
            "不一定是预测错了。",
        ]
    else:
        lines.append("未生成任何样本，见下方“缺失说明”。")
    lines.append("")

    if len(rows) > 1:
        lines += ["## 全部样本排名（按排序分从高到低）", ""]
        lines += [
            "| 排名 | 种子 | 样本 | 平均 pLDDT | pTM | ipTM | 排序分 | 冲突 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for i, row in enumerate(rows[:10], start=1):
            lines.append(
                f"| {i} | {row['seed']} | {row['sample']} | "
                f"{row['avg_plddt']:.2f} | {row['ptm']:.4f} | "
                f"{row['iptm']:.4f} | {row['sample_ranking_score']:.4f} | "
                f"{int(row['has_clash'])} |")
        if len(rows) > 10:
            lines.append("")
            lines.append(f"其余 {len(rows) - 10} 个样本见 `summary.csv`。")
        lines.append("")

    lines += [
        "## pLDDT 怎么读",
        "",
        "| 平均 pLDDT | 含义 |",
        "| ---: | --- |",
        "| > 90 | 很高，主链与侧链均可靠 |",
        "| 70–90 | 高，主链准确 |",
        "| 50–70 | 中等，谨慎对待 |",
        "| < 50 | 低，可能为无序区或不确定 |",
        "",
        "## 注意事项（请先读这节再用数字）",
        "",
        "- OpenFold3 只预测结构与置信度，**不预测结合亲和力**。"
        "需要定量亲和力请用 Boltz-2。",
        "- 排序分只用于同一次任务内给样本排序；不同任务、不同设置下的分数不宜直接比较。",
        "- 样本数多不等于预测更准：先看排名第一的样本，再看多个样本是否一致。",
        "- 预测针对提交的这一个结构；柔性区域、无序蛋白、膜蛋白的预测可信度较低，"
        "请结合 pLDDT 分布判断。",
        "- 模型对输入的质子化状态、金属离子、共价修饰不建模；"
        "配体结合姿态请以 ipTM 与口袋接触为准，不要只看 pLDDT。",
    ]
    if missing_note:
        lines += ["", "## 缺失说明", "", missing_note]
    lines += [
        "",
        "## 输出文件",
        "",
        f"- `predicted.{summary['output_format']}`：排名第一的预测结构。",
        "- `summary.csv`：各样本置信度汇总（按排序分排序）。",
        "- `query.json`：本次生成的 OpenFold3 输入，可复核、可直接拿去跑 `run_openfold predict`。",
        "- `runner.yml`：本次生成的配置（输出格式、随机种子、口袋采样开关）。",
        "- `openfold3_raw/`：OpenFold3 原生输出（各样本结构、置信度 JSON、MSA、timing）。",
        "",
        "## 引用",
        "",
        "- OpenFold Consortium. OpenFold3: A Fully Open Source Biomolecular "
        "Structure Prediction Model Based on AlphaFold3. "
        "https://github.com/aqlaboratory/openfold-3",
        "- Abramson, J. et al. Accurate structure prediction of biomolecular "
        "interactions with AlphaFold 3. Nature (2024). "
        "doi:10.1038/s41586-024-07487-w",
        "- OpenFold3 代码与权重：Apache 2.0；检查点 OpenBind-0 "
        f"（{CKPT_NAME}）。",
    ]
    if "ColabFold" in msa_mode:
        lines += [
            "- MSA 自动生成用 ColabFold 服务器时请引用：Mirdita, M. et al. "
            "ColabFold: making protein folding accessible to all. "
            "Nat. Methods (2022).",
        ]
    lines.append("")
    path = out_dir / "report_zh.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- 运行 OpenFold3

def run_openfold(openfold_cmd: str, query_path: Path, runner_path: Path,
                 ckpt_path: str, out_dir: Path, use_msa_server: bool,
                 use_templates: bool, model_seeds: int,
                 diffusion_samples: int, timeout: int = 7200) -> int:
    """调 run_openfold predict。返回进程退出码；找不到命令时抛 RuntimeError。"""
    cmd = [openfold_cmd, "predict",
           "--query-json", str(query_path),
           "--inference-ckpt-path", ckpt_path,
           "--use-msa-server", "True" if use_msa_server else "False",
           "--use-templates", "True" if use_templates else "False",
           "--num-model-seeds", str(model_seeds),
           "--num-diffusion-samples", str(diffusion_samples),
           "--runner-yaml", str(runner_path),
           "--output-dir", str(out_dir)]
    print("运行命令：" + " ".join(cmd))
    env = dict(os.environ)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"找不到 OpenFold3 可执行文件 '{openfold_cmd}'。请先安装："
            "pip install openfold3==0.5.0（需 GPU），"
            "或使用本仓库的 Dockerfile 构建镜像。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"OpenFold3 运行超时（{timeout} 秒）。该复合物可能过大，"
            "请换更小的结构、减少种子或样本数，或换更大显存的机型。") from exc
    print(proc.stdout[-2000:] if proc.stdout else "")
    if proc.stderr:
        print(proc.stderr[-2000:], file=sys.stderr)
    return proc.returncode


def collect_outputs(out_dir: Path, output_format: str) -> tuple[list[dict], str, str]:
    """收集各样本的置信度，写 summary.csv，复制排名第一的结构。

    静默显存不足防护：只认输出文件是否存在，不认退出码。
    返回（按排序分排好的行列表，排名第一的结构文件名，缺失说明）。
    """
    ext = "cif" if output_format == "cif" else "pdb"
    raw_root = out_dir / QUERY_KEY
    rows: list[dict] = []
    missing: list[str] = []
    agg_re = re.compile(
        rf"^{QUERY_KEY}_seed_(\d+)_sample_(\d+)_confidences_aggregated\.json$")
    if not raw_root.exists():
        missing.append(f"输出目录 {raw_root} 不存在，OpenFold3 未生成任何结果")
    else:
        for agg_path in sorted(raw_root.rglob("*_confidences_aggregated.json")):
            m = agg_re.match(agg_path.name)
            if not m:
                continue
            seed, sample = int(m.group(1)), int(m.group(2))
            try:
                data = parse_aggregated(agg_path)
            except ValueError as exc:
                missing.append(str(exc))
                continue
            model_name = (f"{QUERY_KEY}_seed_{seed}_sample_{sample}"
                          f"_model.{ext}")
            model_path = agg_path.parent / model_name
            if not model_path.exists():
                missing.append(f"样本（种子 {seed}，样本 {sample}）的结构文件缺失")
                continue
            rows.append({
                "seed": seed,
                "sample": sample,
                "structure_file": model_name,
                "model_path": str(model_path),
                "avg_plddt": float(data["avg_plddt"]),
                "ptm": float(data["ptm"]),
                "iptm": float(data["iptm"]),
                "sample_ranking_score": float(data["sample_ranking_score"]),
                "has_clash": float(data["has_clash"]),
                "disorder": (float(data["disorder"])
                             if data.get("disorder") is not None else None),
                "gpde": (float(data["gpde"])
                         if data.get("gpde") is not None else None),
            })
    rows.sort(key=lambda r: r["sample_ranking_score"], reverse=True)
    structure_file = ""
    if rows:
        best_path = Path(rows[0]["model_path"])
        structure_file = f"predicted.{ext}"
        shutil.copy2(best_path, out_dir / structure_file)
    else:
        missing.append("没有任何样本生成结构与置信度")
    write_summary_csv(out_dir, rows)
    if raw_root.exists():
        raw_dir = out_dir / "openfold3_raw"
        raw_dir.mkdir(exist_ok=True)
        for item in raw_root.iterdir():
            dest = raw_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            elif item.is_file():
                shutil.copy2(item, dest)
    note = ""
    if missing:
        note = ("以下输出缺失，任务未完成：" + "；".join(missing) + "。"
                "注意：OpenFold3 在显存不足时可能仍以退出码 0 结束，"
                "请换更小结构、减少种子或样本数，或换更大显存的机型。")
    return rows, structure_file, note


# ---------------------------------------------------------------- 主入口

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="OpenFold3 结构预测（玻尔 App 封装）")
    prot_group = parser.add_mutually_exclusive_group(required=True)
    prot_group.add_argument("--protein-sequence",
                            help="蛋白氨基酸序列（单条链，可含 FASTA 头）")
    prot_group.add_argument("--protein-sequence-file", type=Path,
                            help="含蛋白序列的文件（FASTA 或纯文本）")
    prot_group.add_argument("--pdb-id", help="4 位 PDB 编号，从 RCSB 取第一条链")
    prot_group.add_argument("--pdb-file", type=Path, help="PDB 文件，提取第一条链的序列")
    lig_group = parser.add_mutually_exclusive_group(required=False)
    lig_group.add_argument("--ligand-smiles", help="配体 SMILES")
    lig_group.add_argument("--ligand-sdf-file", type=Path,
                           help="配体 SDF/MOL/MOL2 文件，转成 SMILES 后预测")
    lig_group.add_argument("--ligand-pubchem-cid",
                           help="配体 PubChem 编号，如 2244（运行时从 PubChem 取 SMILES）")
    parser.add_argument("--dna-sequence", help="DNA 序列（A/T/G/C，可含 N）")
    parser.add_argument("--rna-sequence", help="RNA 序列（A/U/G/C，可含 N）")
    parser.add_argument("--modifications",
                        help="残基修饰，如 3:SEP,5:MHO（位置:修饰代码，逗号分隔）")
    parser.add_argument("--pocket",
                        help="口袋约束，如 B|A:45,A:46|4.0（配体链|蛋白链:残基,…|最大距离 Å）")
    parser.add_argument("--msa-file", type=Path,
                        help="自备 .a3m MSA 文件（指定后跳过自动生成）")
    parser.add_argument("--no-msa", action="store_true",
                        help="显式不用 MSA：单序列模式，精度可能下降")
    parser.add_argument("--no-templates", action="store_true",
                        help="不用结构模板（默认用 ColabFold 模板搜索）")
    parser.add_argument("--model-seeds", type=int, default=1,
                        help="模型种子数（默认 1，范围 1–5）")
    parser.add_argument("--diffusion-samples", type=int, default=5,
                        help="每种子扩散样本数（默认 5，范围 1–10）")
    parser.add_argument("--random-seed", type=int, default=None,
                        help="固定随机种子（留空则每次随机）")
    parser.add_argument("--output-format", choices=["cif", "pdb"], default="cif",
                        help="输出结构格式（默认 cif，含完整元数据）")
    parser.add_argument("--out-dir", type=Path, default=Path("./openfold3-output"),
                        help="输出目录（默认 ./openfold3-output）")
    parser.add_argument("--ckpt-path", default=DEFAULT_CKPT_PATH,
                        help="检查点 .pt 文件路径（默认镜像内烤好的 OpenBind-0）")
    parser.add_argument("--openfold-cmd", default="run_openfold",
                        help="OpenFold3 可执行文件名（默认 run_openfold）")
    parser.add_argument("--timeout", type=int, default=7200,
                        help="预测超时秒数（默认 7200）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只验证输入并生成 query.json 与 runner.yml，不实际预测")
    args = parser.parse_args(argv)

    # ---- 输入验证（退出码 2；联网取数失败也是输入错误）
    warnings: list[str] = []
    try:
        protein_source = ""
        if args.protein_sequence is not None:
            raw_seq = args.protein_sequence
            protein_source = "粘贴的序列"
        elif args.protein_sequence_file is not None:
            if not args.protein_sequence_file.exists():
                raise FileNotFoundError(f"序列文件不存在：{args.protein_sequence_file}")
            raw_seq = args.protein_sequence_file.read_text(encoding="utf-8")
            protein_source = f"序列文件 {args.protein_sequence_file.name}"
        elif args.pdb_id is not None:
            raw_seq = fetch_pdb_fasta(args.pdb_id)
            protein_source = f"PDB 编号 {args.pdb_id.strip().upper()}（RCSB）"
            warnings.append(
                "PDB 编号取自 RCSB；节点若无法访问 RCSB，请改用粘贴序列或上传 PDB 文件。")
        else:
            if not args.pdb_file.exists():
                raise FileNotFoundError(f"PDB 文件不存在：{args.pdb_file}")
            raw_seq, protein_source = extract_sequence_from_pdb(args.pdb_file)
        sequence, seq_warnings = validate_protein_sequence(raw_seq)
        warnings.extend(seq_warnings)

        dna_sequence = None
        if args.dna_sequence:
            dna_sequence = validate_nucleic_sequence(args.dna_sequence, "dna")
        rna_sequence = None
        if args.rna_sequence:
            rna_sequence = validate_nucleic_sequence(args.rna_sequence, "rna")

        ligand_smiles = None
        ligand_desc = "无"
        if args.ligand_smiles is not None:
            ligand_smiles = validate_smiles(args.ligand_smiles)
            ligand_desc = "SMILES"
        elif args.ligand_sdf_file is not None:
            if not args.ligand_sdf_file.exists():
                raise FileNotFoundError(f"配体文件不存在：{args.ligand_sdf_file}")
            ligand_smiles, method = sdf_to_smiles(args.ligand_sdf_file)
            ligand_desc = f"SDF 文件（{method} 转换）"
        elif args.ligand_pubchem_cid is not None:
            ligand_smiles = validate_smiles(fetch_pubchem_smiles(args.ligand_pubchem_cid))
            ligand_desc = f"PubChem 编号 {args.ligand_pubchem_cid.strip()}"
            warnings.append(
                "配体 SMILES 取自 PubChem；节点若无法访问 PubChem，请改用粘贴 SMILES 或上传 SDF 文件。")

        modifications = None
        if args.modifications:
            modifications = parse_modifications(args.modifications, len(sequence))

        pocket = None
        pocket_desc = ""
        if args.pocket:
            if ligand_smiles is None:
                raise ValueError("口袋约束需要配体：请先提供配体（SMILES、SDF 文件或 PubChem 编号）。")
            pocket = parse_pocket(args.pocket, len(sequence))
            pocket_desc = ("配体 " + LIGAND_CHAIN + " 靠近残基 "
                           + "、".join(f"{c}{r}" for c, r in pocket["pocket_residues"])
                           + f"，最大距离 {pocket['max_distance']} Å")

        if args.msa_file is not None and args.no_msa:
            raise ValueError("不能同时指定 --msa-file 和 --no-msa：要么上传 .a3m，要么显式不用 MSA。")
        msa_path: str | None = None
        if args.msa_file is not None:
            validate_msa_file(args.msa_file, sequence)
            msa_path = str(args.msa_file.resolve())

        for name, value, lo, hi in (
                ("模型种子数", args.model_seeds, 1, 5),
                ("扩散样本数", args.diffusion_samples, 1, 10)):
            if not lo <= value <= hi:
                raise ValueError(f"{name} {value} 超出范围 {lo}–{hi}。")
        if args.random_seed is not None and args.random_seed < 0:
            raise ValueError(f"随机种子 {args.random_seed} 不能为负数。")
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"错误：读取输入文件失败：{exc}", file=sys.stderr)
        return 2

    # ---- MSA 模式（三条分支显式处理，不漏原生默认）
    if msa_path is not None:
        msa_mode = f"上传 .a3m（{args.msa_file.name}），跳过自动生成"
        use_msa_server = False
        use_msas = True
        msa_note = ""
    elif args.no_msa:
        msa_mode = "单序列模式（未使用 MSA）"
        use_msa_server = False
        use_msas = False
        msa_note = "未使用 MSA，精度可能下降；有同源物的天然蛋白建议用自动生成 MSA 重跑。"
        warnings.append(msa_note)
    else:
        msa_mode = f"自动生成（{DEFAULT_MSA_SERVER_URL}）"
        use_msa_server = True
        use_msas = True
        msa_note = ""
    templates_on = not args.no_templates
    if not templates_on:
        warnings.append("已关闭结构模板；模板搜索是默认开启的，关闭后精度可能下降。")
    if not use_msa_server and templates_on:
        warnings.append(
            "未生成 MSA 时模板搜索无效（模板随 MSA 一起生成），"
            "本次“使用模板”开关不起作用。")

    composition_parts = [f"蛋白 {len(sequence)} 个残基（{PROTEIN_CHAIN} 链）"]
    if ligand_smiles is not None:
        composition_parts.append(f"配体（{LIGAND_CHAIN} 链，{ligand_desc}）")
    if dna_sequence is not None:
        composition_parts.append(f"DNA {len(dna_sequence)} 个碱基（{DNA_CHAIN} 链）")
    if rna_sequence is not None:
        composition_parts.append(f"RNA {len(rna_sequence)} 个碱基（{RNA_CHAIN} 链）")

    summary = {
        "protein_len": len(sequence),
        "protein_source": protein_source,
        "composition": " + ".join(composition_parts),
        "model_seeds": args.model_seeds,
        "diffusion_samples": args.diffusion_samples,
        "output_format": args.output_format,
        "pocket_desc": pocket_desc,
        "random_seed": args.random_seed,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    query = build_query(sequence, ligand_smiles, dna_sequence, rna_sequence,
                        modifications, pocket, msa_path, use_msas)
    query_path = args.out_dir / "query.json"
    query_path.write_text(json.dumps(query, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    runner_text = build_runner_yaml(args.output_format, args.random_seed,
                                    pocket is not None)
    runner_path = args.out_dir / "runner.yml"
    runner_path.write_text(runner_text, encoding="utf-8")
    print(f"输入已生成：{query_path}、{runner_path}")
    print(f"蛋白 {len(sequence)} 个残基；复合物：{summary['composition']}；"
          f"MSA：{msa_mode}；模板：{'开启' if templates_on else '关闭'}")
    for w in warnings:
        print(f"提示：{w}")

    if args.dry_run:
        print("试运行模式：只生成输入文件，不实际预测。")
        return 0

    try:
        code = run_openfold(args.openfold_cmd, query_path, runner_path,
                            args.ckpt_path, args.out_dir, use_msa_server,
                            templates_on, args.model_seeds,
                            args.diffusion_samples, timeout=args.timeout)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    # 静默显存不足防护：只认输出文件，不认退出码
    rows, structure_file, missing_note = collect_outputs(
        args.out_dir, args.output_format)
    write_report(args.out_dir, summary, rows, msa_mode, templates_on,
                 warnings, missing_note=missing_note)
    if code != 0:
        print(f"警告：OpenFold3 退出码 {code}（非 0），但已按输出文件判定结果。",
              file=sys.stderr)
    if missing_note:
        print(f"错误：{missing_note}", file=sys.stderr)
        return 3
    if rows:
        best = rows[0]
        print(f"完成：共 {len(rows)} 个样本；排名第一：种子 {best['seed']} 样本 "
              f"{best['sample']}，平均 pLDDT {best['avg_plddt']:.2f}，"
              f"pTM {best['ptm']:.4f}，ipTM {best['iptm']:.4f}")
    print(f"输出目录：{args.out_dir.resolve()}")
    print(f"  - predicted.{args.output_format}\n  - summary.csv\n"
          "  - report_zh.md\n  - openfold3_raw/（原生输出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
