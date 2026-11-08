#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_boltz2.py — Boltz-2 蛋白-配体共折叠 + 亲和力预测的命令行封装

用途：给玻尔（Bohrium）App / 本地使用。只调用本地 `boltz`，不调用任何
第三方 API，不使用任何密钥；唯一的网络访问是默认用公开 ColabFold 服务
器自动生成 MSA（--use_msa_server），以及镜像构建时下载权重。

输入（单配体）：
  --sequence SEQ | --sequence-file FILE   蛋白氨基酸序列（单条链，FASTA 或纯文本）
  --ligand-smiles SMILES | --ligand-ccd CCD   配体（二选一，优先 SMILES）
  --msa-file FILE     自备 .a3m MSA（可选；指定后跳过自动生成）
  --no-msa            显式单序列模式（不推荐，精度可能下降）

输出（--out-dir，默认 ./boltz2-output）：
  input.yaml        生成的 Boltz 输入（可复核、可直接拿去跑 boltz predict）
  predicted.pdb     排名第一的预测结构（或 .cif，见 --output-format）
  confidence.json   置信度（confidence_score、pLDDT、ipTM、ligand_iptm）
  affinity.json     亲和力（仅排名第一的结构；默认开启）
  report_zh.md      中文解读报告（置信度、亲和力换算、注意事项）
  boltz_raw/        Boltz 原生输出（结构、置信度、亲和力 JSON、PAE/PDE/NPZ）

Boltz 原生命令（供参考）：
  boltz predict input.yaml --use_msa_server --out_dir OUT --cache CACHE \
      --recycling_steps 3 --sampling_steps 200 --diffusion_samples 1 \
      --step_scale 1.5 --output_format pdb \
      --sampling_steps_affinity 200 --diffusion_samples_affinity 5 \
      --max_msa_seqs 8192 --override

退出码：
  0  成功（结构 + 置信度 + 亲和力齐全；亲和力关闭或配体超大时只要求结构 + 置信度）
  2  输入错误（序列非法、SMILES 非法、配体超限、MSA 不匹配等）
  3  boltz 未安装或运行失败（含静默显存不足：退出码为 0 但无输出文件）

Boltz-2 版本：只用 v2.2.1（代码与权重均为 MIT）。2.1 只走托管 API，不在
MIT 发布范围内，本封装不用。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BOLTZ_VERSION = "2.2.1"
PROTEIN_CHAIN = "A"
LIGAND_CHAIN = "B"

MAX_RESIDUES = 2900
WARN_RESIDUES = 1500
MAX_AFFINITY_HEAVY_ATOMS = 128
WARN_AFFINITY_HEAVY_ATOMS = 56

DEFAULT_MSA_SERVER_URL = "https://api.colabfold.com"

# 20 种标准氨基酸 + X（未知）。其余字母（B/J/O/U/Z 等）一律拒绝。
SEQUENCE_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYX]+$")
SMILES_CHAR_RE = re.compile(r"^[A-Za-z0-9\[\]()=#+\-/\\@%.*~$]+$")

# 亲和力换算：affinity_pred_value = log10(IC50)，IC50 单位 μM。
# -3 ≈ 1 nM、-2 ≈ 10 nM、-1 ≈ 100 nM、0 ≈ 1 μM、1 ≈ 10 μM、2 ≈ 100 μM。
AFFINITY_CONVERSION = [
    (-3, "约 1 nM"),
    (-2, "约 10 nM"),
    (-1, "约 100 nM"),
    (0, "约 1 μM"),
    (1, "约 10 μM"),
    (2, "约 100 μM"),
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


def validate_sequence(sequence: str) -> tuple[str, list[str]]:
    """返回（清洗后的序列，警告列表）。非法时抛 ValueError。"""
    sequence = clean_sequence(sequence)
    if not sequence:
        raise ValueError("蛋白序列为空。请粘贴氨基酸序列或用 --sequence-file 传入 FASTA 文件。")
    if len(sequence) > MAX_RESIDUES:
        raise ValueError(
            f"蛋白序列共 {len(sequence)} 个残基，超过上限 {MAX_RESIDUES}。"
            "Boltz 无法预测这么大的复合物，请换更小的结构或分段提交。")
    bad = sorted(set(sequence) - set("ACDEFGHIKLMNPQRSTVWYX"))
    if bad:
        raise ValueError(
            f"蛋白序列含非法字符：{''.join(bad)}。只接受 20 种标准氨基酸字母"
            "（ACDEFGHIKLMNPQRSTVWY）加 X（未知）。")
    if not SEQUENCE_RE.match(sequence):
        raise ValueError("蛋白序列格式不对。请检查是否混入数字、空格或非氨基酸字符。")
    warnings: list[str] = []
    if len(sequence) > WARN_RESIDUES:
        warnings.append(
            f"蛋白共 {len(sequence)} 个残基，超过 {WARN_RESIDUES}，"
            "需要更大显存的机型（建议 40 GB 以上），默认 24 GB 机型可能显存不足。")
    return sequence, warnings


def _count_heavy_atoms_fallback(smiles: str) -> int:
    """无 RDKit 时的 SMILES 重原子计数：方括号原子计 1 个（H 除外），
    有机子集字母（B/C/N/O/P/S/F/Cl/Br/I，含芳香小写）各计 1 个。"""
    count = 0
    i, n = 0, len(smiles)
    while i < n:
        ch = smiles[i]
        if ch == "[":
            j = smiles.find("]", i)
            if j == -1:
                raise ValueError(f"SMILES 方括号未闭合：{smiles}")
            inner = smiles[i + 1:j]
            m = re.match(r"\d*([A-Za-z][a-z]?)", inner)
            elem = m.group(1).capitalize() if m else ""
            if elem and elem != "H":
                count += 1
            i = j + 1
        elif i + 1 < n and smiles[i:i + 2] in ("Cl", "Br"):
            count += 1
            i += 2
        elif ch in "BCNOPSFIcnopsb":
            count += 1
            i += 1
        else:
            i += 1
    return count


def count_heavy_atoms(smiles: str) -> tuple[int, str]:
    """返回（重原子数，计数方式）。有 RDKit 时用它（与 Boltz 的口径一致，
    即 RDKit RemoveHs 后的重原子数）；无 RDKit 时用内置分词器近似。"""
    try:
        from rdkit import Chem  # type: ignore

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"SMILES 无法解析：{smiles}")
        return mol.GetNumHeavyAtoms(), "RDKit"
    except ImportError:
        return _count_heavy_atoms_fallback(smiles), "内置分词器（无 RDKit 时的近似值）"


def validate_smiles(smiles: str) -> tuple[int, list[str]]:
    """返回（重原子数，警告列表）。非法时抛 ValueError。"""
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
        raise ValueError(f"SMILES 方括号不配对：{smiles}")
    heavy, method = count_heavy_atoms(smiles)
    if heavy == 0:
        raise ValueError(f"SMILES 没有重原子：{smiles}")
    warnings: list[str] = []
    if heavy > MAX_AFFINITY_HEAVY_ATOMS:
        warnings.append(
            f"配体重原子 {heavy} 个，超过亲和力上限 {MAX_AFFINITY_HEAVY_ATOMS}，"
            "只做结构预测，不计算亲和力。")
    elif heavy > WARN_AFFINITY_HEAVY_ATOMS:
        warnings.append(
            f"配体重原子 {heavy} 个，超过作者建议的 {WARN_AFFINITY_HEAVY_ATOMS}，"
            "亲和力结果仅供参考。")
    return heavy, warnings


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


def _yaml_quote(value: str) -> str:
    """YAML 单引号字符串：单引号加倍。"""
    return "'" + value.replace("'", "''") + "'"


def build_yaml(sequence: str, ligand_smiles: str | None, ligand_ccd: str | None,
               msa_path: str | None, no_msa: bool,
               pocket_contacts: list[tuple[str, int]] | None,
               pocket_max_distance: float, affinity: bool) -> str:
    """生成 Boltz 输入 YAML（手写，不依赖 PyYAML）。"""
    lines = ["version: 1", "sequences:"]
    protein = ["  - protein:", f"      id: {PROTEIN_CHAIN}",
               f"      sequence: {sequence}"]
    if msa_path is not None:
        protein.append(f"      msa: {msa_path}")
    elif no_msa:
        protein.append("      msa: empty")
    # 默认（自动生成 MSA）时不写 msa 字段，由 --use_msa_server 生成。
    lines.extend(protein)
    if ligand_smiles is not None:
        lines += ["  - ligand:", f"      id: {LIGAND_CHAIN}",
                  f"      smiles: {_yaml_quote(ligand_smiles)}"]
    else:
        lines += ["  - ligand:", f"      id: {LIGAND_CHAIN}",
                  f"      ccd: {ligand_ccd}"]
    if pocket_contacts:
        contacts = ", ".join(f"[{chain}, {res}]" for chain, res in pocket_contacts)
        lines += ["constraints:",
                  "  - pocket:",
                  f"      binder: {LIGAND_CHAIN}",
                  f"      contacts: [{contacts}]",
                  f"      max_distance: {pocket_max_distance}"]
    if affinity:
        lines += ["properties:", "  - affinity:", f"      binder: {LIGAND_CHAIN}"]
    return "\n".join(lines) + "\n"


def parse_pocket(value: str, sequence_len: int) -> list[tuple[str, int]]:
    """解析 --pocket-contacts，形如 "A:45,A:46,A:120"。"""
    contacts: list[tuple[str, int]] = []
    for item in value.split(","):
        item = item.strip()
        m = re.match(r"^([A-Za-z]):(\d+)$", item)
        if not m:
            raise ValueError(
                f"口袋约束格式不对：{item}（应为 链:残基号，如 A:45，多个用逗号分隔）。")
        chain, res = m.group(1).upper(), int(m.group(2))
        if chain != PROTEIN_CHAIN:
            raise ValueError(
                f"口袋约束只支持蛋白链 {PROTEIN_CHAIN}，不支持链 {chain}。")
        if not 1 <= res <= sequence_len:
            raise ValueError(
                f"口袋残基号 {res} 超出蛋白长度 {sequence_len}。")
        contacts.append((chain, res))
    if not contacts:
        raise ValueError("口袋约束为空。")
    return contacts


# ---------------------------------------------------------------- 输出解析

def parse_confidence(path: Path) -> dict:
    """解析 Boltz 置信度 JSON。缺关键字段时抛 ValueError。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"置信度 JSON 无法解析：{path}（{exc}）") from exc
    for key in ("confidence_score", "complex_plddt", "iptm", "ligand_iptm"):
        if key not in data:
            raise ValueError(f"置信度 JSON 缺少字段 {key}：{path}")
    return data


def parse_affinity(path: Path) -> dict:
    """解析 Boltz 亲和力 JSON。缺关键字段时抛 ValueError。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"亲和力 JSON 无法解析：{path}（{exc}）") from exc
    for key in ("affinity_pred_value", "affinity_probability_binary"):
        if key not in data:
            raise ValueError(f"亲和力 JSON 缺少字段 {key}：{path}")
    return data


def affinity_to_ic50_um(value: float) -> float:
    """affinity_pred_value = log10(IC50)，IC50 单位 μM。"""
    return 10.0 ** value


def write_report(out_dir: Path, summary: dict, confidence: dict | None,
                 affinity: dict | None, msa_mode: str, msa_note: str,
                 warnings: list[str], affinity_expected: bool,
                 affinity_missing_note: str = "") -> Path:
    """写中文解读报告 report_zh.md。"""
    lines = ["# Boltz-2 蛋白-配体共折叠与亲和力预测报告", ""]
    lines += [
        f"- 蛋白：{summary['sequence_len']} 个残基（{PROTEIN_CHAIN} 链）",
        f"- 配体：{summary['ligand_desc']}",
        f"- MSA：{msa_mode}",
        f"- 模型：Boltz-2 v{BOLTZ_VERSION}（MIT）",
        f"- 设置：样本 {summary['diffusion_samples']}、循环 {summary['recycling_steps']}、"
        f"采样步 {summary['sampling_steps']}、步长 {summary['step_scale']}、"
        f"亲和力样本 {summary['affinity_samples']}、亲和力采样步 {summary['affinity_steps']}",
    ]
    if summary.get("pocket_desc"):
        lines.append(f"- 口袋约束：{summary['pocket_desc']}")
    lines.append("")
    if warnings:
        lines += ["## 提示", ""]
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines += ["## 结构", ""]
    structure_file = summary.get("structure_file", "")
    if structure_file:
        lines.append(f"预测结构：`{structure_file}`（排名第一的样本）。"
                     "用 PyMOL 或 Mol* 打开查看。")
    else:
        lines.append("未生成预测结构，见下方“缺失说明”。")
    lines.append("")

    lines += ["## 置信度", ""]
    if confidence is not None:
        cs = confidence["confidence_score"]
        plddt = confidence["complex_plddt"]
        iptm = confidence["iptm"]
        lig_iptm = confidence["ligand_iptm"]
        lines += [
            "| 指标 | 数值 | 说明 |",
            "| --- | ---: | --- |",
            f"| confidence_score | {cs:.4f} | 综合分 = 0.8×pLDDT + 0.2×ipTM，只用于同一次任务内给样本排序 |",
            f"| pLDDT | {plddt:.4f} | 复合物平均 pLDDT，越高结构越可信 |",
            f"| ipTM | {iptm:.4f} | 界面 TM 分，评排布的置信度，不是结合强度 |",
            f"| ligand_iptm | {lig_iptm:.4f} | 蛋白-配体界面的 ipTM，看配体姿态放得对不对 |",
            "",
            "解读：高 pLDDT 不代表链或配体放对了位置，要看 ipTM 与 ligand_iptm；"
            "多个样本间折叠、界面、配体姿态一致，比单个高分更可信。",
        ]
    else:
        lines.append("未生成置信度文件，见下方“缺失说明”。")
    lines.append("")

    lines += ["## 亲和力（仅排名第一的结构）", ""]
    if affinity is not None:
        prob = affinity["affinity_probability_binary"]
        value = affinity["affinity_pred_value"]
        ic50 = affinity_to_ic50_um(value)
        pic50 = 6.0 - value
        kcal = (6.0 - value) * 1.364
        if ic50 >= 1:
            ic50_str = f"{ic50:.2f} μM"
        elif ic50 >= 0.001:
            ic50_str = f"{ic50 * 1000:.1f} nM"
        else:
            ic50_str = f"{ic50 * 1_000_000:.1f} pM"
        lines += [
            "| 指标 | 数值 | 用途 |",
            "| --- | ---: | --- |",
            f"| 结合概率 affinity_probability_binary | {prob:.3f} | 0–1，用于区分结合物与诱饵（苗头发现） |",
            f"| 预测亲和力 affinity_pred_value | {value:.3f} | log10(IC50)，单位 μM，越负结合越强，用于相关化合物排序 |",
            f"| 换算 IC50 | {ic50_str} | 由 10^预测值换算，仅为模型估计 |",
            f"| pIC50 | {pic50:.2f} | 6 − 预测值 |",
            f"| 结合自由能估计 | {kcal:.2f} kcal/mol | (6 − 预测值) × 1.364，越高越强 |",
            "",
            "换算表（log10 IC50 → IC50）：",
            "",
            "| 预测值 | 约合 IC50 |",
            "| ---: | ---: |",
        ]
        for v, desc in AFFINITY_CONVERSION:
            mark = " ← 本次结果" if abs(value - v) < 0.5 else ""
            lines.append(f"| {v} | {desc}{mark} |")
        v1 = affinity.get("affinity_pred_value1")
        v2 = affinity.get("affinity_pred_value2")
        if v1 is not None and v2 is not None:
            lines += [
                "",
                f"集成模型分头值：模型 1 为 {v1:.3f}，模型 2 为 {v2:.3f}。"
                + ("两个分头值分歧较大，本次亲和力估计不稳定，请谨慎使用。"
                   if abs(v1 - v2) > 1.0 else "两个分头值接近，估计相对稳定。"),
            ]
    elif affinity_expected:
        lines.append("亲和力未生成。" + (affinity_missing_note or
                                       "结构已生成，但亲和力模型未输出结果。"))
    else:
        lines.append("本次未计算亲和力（已关闭，或配体超出亲和力上限，只做结构预测）。")
    lines.append("")

    lines += [
        "## 注意事项（请先读这节再用数字）",
        "",
        "- 亲和力是模型预测值，**不是实验测得的 Kd / IC50**，只用于同一靶点、"
        "相同设置下相关化合物的排序；不要用它区分活性与非活性，那是结合概率的工作。",
        "- 结合概率没有通用阈值：一个靶点上有效的阈值未必能迁移到另一个靶点。"
        "先拿靶点上几个已知活性化合物校准，再信任未知化合物的排序。",
        "- ipTM 评的是排布的置信度，不是结合强度；口袋或姿态错了，数值再好看也没意义。",
        "- 亲和力只针对一个配体（本任务的配体链），辅因子、离子等只影响结构，不参与打分；"
        "蛋白-蛋白、DNA/RNA 没有亲和力估计。",
        "- 亲和力头是在 IC50、Ki、Kd 等放在同一对数标度上的数据上训练的，"
        "不同实验、不同条件下的数值不宜直接比较。",
    ]
    if msa_note:
        lines += ["", f"- {msa_note}"]
    lines += [
        "",
        "## 输出文件",
        "",
        "- `predicted.pdb`：排名第一的预测结构（或 `predicted.cif`，见 --output-format）。",
        "- `confidence.json`：置信度；`affinity.json`：亲和力（未计算时没有此文件）。",
        "- `input.yaml`：本次生成的 Boltz 输入，可复核、可直接拿去跑 `boltz predict`。",
        "- `boltz_raw/`：Boltz 原生输出（各样本结构、置信度、亲和力 JSON、PAE/PDE/NPZ）。",
        "",
        "## 引用",
        "",
        "- Passaro, S. et al. Boltz-2: Towards Accurate and Efficient Binding Affinity "
        "Prediction. bioRxiv (2025). doi:10.1101/2025.06.14.659707",
        "- Boltz-2 代码与权重：MIT 许可；https://github.com/jwohlwend/boltz",
        "- 权重：Hugging Face boltz-community/boltz-2",
        "- MSA 自动生成用 ColabFold 服务器时请引用：Mirdita, M. et al. ColabFold: "
        "making protein folding accessible to all. Nat. Methods (2022).",
        "",
    ]
    path = out_dir / "report_zh.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

# ---------------------------------------------------------------- 运行 Boltz

def run_boltz(boltz_cmd: str, yaml_path: Path, out_dir: Path, cache_dir: str,
              use_msa_server: bool, msa_server_url: str, use_potentials: bool,
              recycling: int, sampling: int, samples: int, step_scale: float,
              output_format: str, affinity_samples: int, affinity_steps: int,
              timeout: int = 3600) -> int:
    """调 boltz predict。返回进程退出码；找不到 boltz 时抛 RuntimeError。"""
    cmd = [boltz_cmd, "predict", str(yaml_path),
           "--out_dir", str(out_dir),
           "--cache", cache_dir,
           "--recycling_steps", str(recycling),
           "--sampling_steps", str(sampling),
           "--diffusion_samples", str(samples),
           "--step_scale", str(step_scale),
           "--output_format", output_format,
           "--sampling_steps_affinity", str(affinity_steps),
           "--diffusion_samples_affinity", str(affinity_samples),
           "--max_msa_seqs", "8192",
           "--override"]
    if use_msa_server:
        cmd += ["--use_msa_server", "--msa_server_url", msa_server_url]
    if use_potentials:
        cmd += ["--use_potentials"]
    print("运行命令：" + " ".join(cmd))
    env = dict(os.environ)
    env["BOLTZ_CACHE"] = cache_dir
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"找不到 Boltz 可执行文件 '{boltz_cmd}'。请先安装："
            "pip install 'boltz[cuda]==2.2.1'（需 GPU），"
            "或使用本仓库的 Dockerfile 构建镜像。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Boltz 运行超时（{timeout} 秒）。该复合物可能过大，"
            "请换更小的结构、减少样本数，或换更大显存的机型。") from exc
    print(proc.stdout[-2000:] if proc.stdout else "")
    if proc.stderr:
        print(proc.stderr[-2000:], file=sys.stderr)
    return proc.returncode


def collect_outputs(out_dir: Path, stem: str, output_format: str,
                    affinity_expected: bool) -> tuple[dict | None, dict | None,
                                                      str, str]:
    """静默显存不足防护：只认输出文件是否存在，不认退出码。

    返回（置信度，亲和力，结构文件名，缺失说明）。结构或置信度缺失时，
    置信度返回 None，调用方按失败处理。"""
    ext = "pdb" if output_format == "pdb" else "cif"
    pred_dir = out_dir / "predictions" / stem
    missing: list[str] = []
    structure_src = pred_dir / f"{stem}_model_0.{ext}"
    confidence_src = pred_dir / f"confidence_{stem}_model_0.json"
    affinity_src = pred_dir / f"affinity_{stem}.json"

    structure_file = ""
    if structure_src.exists():
        structure_file = f"predicted.{ext}"
        shutil.copy2(structure_src, out_dir / structure_file)
    else:
        missing.append(f"预测结构 {structure_src.name} 未生成")

    confidence = None
    if confidence_src.exists():
        shutil.copy2(confidence_src, out_dir / "confidence.json")
        try:
            confidence = parse_confidence(confidence_src)
        except ValueError as exc:
            missing.append(str(exc))
    else:
        missing.append(f"置信度文件 {confidence_src.name} 未生成")

    affinity = None
    if affinity_expected:
        if affinity_src.exists():
            shutil.copy2(affinity_src, out_dir / "affinity.json")
            try:
                affinity = parse_affinity(affinity_src)
            except ValueError as exc:
                missing.append(str(exc))
        else:
            missing.append(f"亲和力文件 {affinity_src.name} 未生成")

    # 原生输出原样保留一份
    if pred_dir.exists():
        raw_dir = out_dir / "boltz_raw"
        raw_dir.mkdir(exist_ok=True)
        for item in pred_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, raw_dir / item.name)

    note = ""
    if missing:
        note = ("以下输出缺失，任务未完成：" + "；".join(missing) + "。"
                "注意：Boltz 在显存不足时可能仍以退出码 0 结束，"
                "请换更小结构、减少样本数，或换更大显存的机型。")
    return confidence, affinity, structure_file, note


# ---------------------------------------------------------------- 主入口

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Boltz-2 蛋白-配体共折叠 + 亲和力预测（玻尔 App 封装）")
    seq_group = parser.add_mutually_exclusive_group(required=True)
    seq_group.add_argument("--sequence", help="蛋白氨基酸序列（单条链，可含 FASTA 头）")
    seq_group.add_argument("--sequence-file", type=Path, help="含蛋白序列的文件（FASTA 或纯文本）")
    lig_group = parser.add_mutually_exclusive_group(required=True)
    lig_group.add_argument("--ligand-smiles", help="配体 SMILES")
    lig_group.add_argument("--ligand-ccd", help="配体 CCD 编号，如 ATP（与 SMILES 二选一）")
    parser.add_argument("--msa-file", type=Path, help="自备 .a3m MSA 文件（指定后跳过自动生成）")
    parser.add_argument("--no-msa", action="store_true",
                        help="显式单序列模式：不生成也不用 MSA，精度可能下降")
    parser.add_argument("--out-dir", type=Path, default=Path("./boltz2-output"),
                        help="输出目录（默认 ./boltz2-output）")
    parser.add_argument("--output-format", choices=["pdb", "mmcif"], default="pdb",
                        help="输出结构格式（默认 pdb，便于后续接 PLIP 分析）")
    parser.add_argument("--diffusion-samples", type=int, default=1,
                        help="结构样本数（默认 1，范围 1–20）")
    parser.add_argument("--recycling-steps", type=int, default=3,
                        help="循环精修次数（默认 3，范围 1–10）")
    parser.add_argument("--sampling-steps", type=int, default=200,
                        help="结构采样步数（默认 200，范围 50–500）")
    parser.add_argument("--step-scale", type=float, default=1.5,
                        help="采样步长（默认 1.5，范围 1–2，越小多样性越高）")
    parser.add_argument("--affinity-samples", type=int, default=5,
                        help="亲和力样本数（默认 5，范围 1–20）")
    parser.add_argument("--affinity-steps", type=int, default=200,
                        help="亲和力采样步数（默认 200，范围 50–500）")
    parser.add_argument("--no-affinity", action="store_true", help="不计算亲和力，只做结构预测")
    parser.add_argument("--use-potentials", action="store_true",
                        help="推理时加势能（构象物理合理性更好，耗时更长）")
    parser.add_argument("--pocket-contacts",
                        help="口袋约束，如 A:45,A:46,A:120（链:残基号，逗号分隔）")
    parser.add_argument("--pocket-max-distance", type=float, default=6.0,
                        help="口袋约束最大距离，单位 Å（默认 6.0，范围 4–20）")
    parser.add_argument("--msa-server-url", default=DEFAULT_MSA_SERVER_URL,
                        help="MSA 服务器地址（默认公开 ColabFold 服务器）")
    parser.add_argument("--boltz-cmd", default="boltz", help="Boltz 可执行文件名（默认 boltz）")
    parser.add_argument("--cache-dir",
                        help="权重缓存目录（默认 BOLTZ_CACHE 环境变量或 ~/.boltz）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只验证输入并生成 input.yaml，不实际预测")
    args = parser.parse_args(argv)

    # ---- 输入验证（退出码 2）
    try:
        if args.sequence_file is not None and not args.sequence_file.exists():
            raise FileNotFoundError(f"序列文件不存在：{args.sequence_file}")
        raw_seq = args.sequence if args.sequence is not None \
            else args.sequence_file.read_text(encoding="utf-8")
        sequence, warnings = validate_sequence(raw_seq)

        heavy_atoms = None
        ligand_desc = ""
        if args.ligand_smiles is not None:
            heavy_atoms, lig_warnings = validate_smiles(args.ligand_smiles)
            warnings.extend(lig_warnings)
            ligand_desc = f"SMILES（重原子 {heavy_atoms} 个）"
        else:
            ccd = args.ligand_ccd.strip().upper()
            if not re.match(r"^[A-Z0-9]{3,4}$", ccd):
                raise ValueError(f"CCD 编号格式不对：{args.ligand_ccd}（应为 3–4 位字母数字，如 ATP）。")
            ligand_desc = f"CCD {ccd}"

        if args.msa_file is not None and args.no_msa:
            raise ValueError("不能同时指定 --msa-file 和 --no-msa：要么上传 .a3m，要么显式不用 MSA。")
        msa_path: str | None = None
        if args.msa_file is not None:
            validate_msa_file(args.msa_file, sequence)
            msa_path = str(args.msa_file.resolve())

        pocket_contacts = None
        pocket_desc = ""
        if args.pocket_contacts:
            pocket_contacts = parse_pocket(args.pocket_contacts, len(sequence))
            if not 4.0 <= args.pocket_max_distance <= 20.0:
                raise ValueError(
                    f"口袋最大距离 {args.pocket_max_distance} 超出范围 4–20 Å。")
            pocket_desc = ("残基 " + "、".join(f"{c}{r}" for c, r in pocket_contacts)
                           + f"，最大距离 {args.pocket_max_distance} Å")

        for name, value, lo, hi in (
                ("样本数", args.diffusion_samples, 1, 20),
                ("循环次数", args.recycling_steps, 1, 10),
                ("采样步数", args.sampling_steps, 50, 500),
                ("亲和力样本数", args.affinity_samples, 1, 20),
                ("亲和力采样步数", args.affinity_steps, 50, 500)):
            if not lo <= value <= hi:
                raise ValueError(f"{name} {value} 超出范围 {lo}–{hi}。")
        if not 1.0 <= args.step_scale <= 2.0:
            raise ValueError(f"步长 {args.step_scale} 超出范围 1–2。")
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"错误：读取输入文件失败：{exc}", file=sys.stderr)
        return 2

    # ---- MSA 模式（三条分支显式处理，不漏原生默认）
    if args.msa_file is not None:
        msa_mode = f"上传 .a3m（{args.msa_file.name}），跳过自动生成"
        use_msa_server = False
        msa_note = ""
    elif args.no_msa:
        msa_mode = "单序列模式（未使用 MSA）"
        use_msa_server = False
        msa_note = "未使用 MSA，精度可能下降；有同源物的天然蛋白建议用自动生成 MSA 重跑。"
        warnings.append(msa_note)
    else:
        msa_mode = f"自动生成（{args.msa_server_url}）"
        use_msa_server = True
        msa_note = ""

    # ---- 亲和力开关
    affinity_on = not args.no_affinity
    if affinity_on and heavy_atoms is not None and heavy_atoms > MAX_AFFINITY_HEAVY_ATOMS:
        affinity_on = False
        warnings.append("配体超大，本次只做结构预测，不计算亲和力。")

    summary = {
        "sequence_len": len(sequence),
        "ligand_desc": ligand_desc,
        "diffusion_samples": args.diffusion_samples,
        "recycling_steps": args.recycling_steps,
        "sampling_steps": args.sampling_steps,
        "step_scale": args.step_scale,
        "affinity_samples": args.affinity_samples,
        "affinity_steps": args.affinity_steps,
        "pocket_desc": pocket_desc,
        "structure_file": "",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    yaml_text = build_yaml(sequence,
                           args.ligand_smiles, args.ligand_ccd,
                           msa_path, args.no_msa,
                           pocket_contacts, args.pocket_max_distance,
                           affinity_on)
    yaml_path = args.out_dir / "input.yaml"
    yaml_path.write_text(yaml_text, encoding="utf-8")
    print(f"输入 YAML 已生成：{yaml_path}")
    print(f"蛋白 {len(sequence)} 个残基；配体：{ligand_desc}；"
          f"MSA：{msa_mode}；亲和力：{'开启' if affinity_on else '关闭'}")
    for w in warnings:
        print(f"提示：{w}")

    if args.dry_run:
        print("试运行模式：只生成 YAML，不实际预测。")
        return 0

    cache_dir = (args.cache_dir or os.environ.get("BOLTZ_CACHE")
                 or str(Path.home() / ".boltz"))
    stem = "input"
    try:
        code = run_boltz(args.boltz_cmd, yaml_path, args.out_dir, cache_dir,
                         use_msa_server, args.msa_server_url, args.use_potentials,
                         args.recycling_steps, args.sampling_steps,
                         args.diffusion_samples, args.step_scale,
                         args.output_format, args.affinity_samples,
                         args.affinity_steps)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    # 静默显存不足防护：只认输出文件，不认退出码
    confidence, affinity, structure_file, missing_note = collect_outputs(
        args.out_dir, stem, args.output_format, affinity_on)
    summary["structure_file"] = structure_file
    write_report(args.out_dir, summary, confidence, affinity,
                 msa_mode, msa_note, warnings, affinity_on,
                 affinity_missing_note=missing_note)
    if code != 0:
        print(f"警告：Boltz 退出码 {code}（非 0），但已按输出文件判定结果。", file=sys.stderr)
    if missing_note:
        print(f"错误：{missing_note}", file=sys.stderr)
        return 3
    if confidence is not None:
        print(f"完成：confidence_score {confidence['confidence_score']:.4f}，"
              f"pLDDT {confidence['complex_plddt']:.4f}，ipTM {confidence['iptm']:.4f}")
    if affinity is not None:
        print(f"亲和力：结合概率 {affinity['affinity_probability_binary']:.3f}，"
              f"预测 log10(IC50) {affinity['affinity_pred_value']:.3f}")
    print(f"输出目录：{args.out_dir.resolve()}")
    print("  - predicted.pdb / predicted.cif\n  - confidence.json\n"
          "  - affinity.json\n  - report_zh.md\n  - boltz_raw/（原生输出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
