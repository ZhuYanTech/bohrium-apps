#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launching.py — OpenFold3 结构预测的 DP-Launching 入口（标准离线任务型）

玻尔开发者中心创建 App 时选“标准离线任务”，新建版本时 EntryPoint 填
镜像里的绝对路径：/app/launching.py。

作用：把 run_openfold3.py 的命令行封装成 Launching 声明式入口。
Launching 在建版本时按 OpenFold3Options 的声明自动生成 JSON Schema，
展开成用户填表界面（蛋白 / 配体 / DNA / RNA / 修饰 / 口袋 / MSA / 采样参数），
再把用户填的参数以命令行参数形式传回本文件，main() 转调 run_openfold3.main()。

不预测结合亲和力（需亲和力请用 Boltz-2）。

引用：
- OpenFold Consortium. OpenFold3: A Fully Open Source Biomolecular Structure
  Prediction Model Based on AlphaFold3. https://github.com/aqlaboratory/openfold-3
- Abramson, J. et al. Accurate structure prediction of biomolecular interactions
  with AlphaFold 3. Nature (2024). doi:10.1038/s41586-024-07487-w

本文件不调用任何第三方 API、不含密钥；唯一的网络访问是 run_openfold3.py
在用户要求时从 RCSB / PubChem 取数，以及默认用公开 ColabFold 服务器
自动生成 MSA（可在表单里关掉，改传 .a3m）。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional

# 让 run_openfold3.py 能从同目录导入（无论从哪里启动本文件）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import (
    BaseModel,
    Field,
    InputFilePath,
    OutputDirectory,
)

import run_openfold3  # noqa: E402  (在 sys.path 调整之后导入)


class OpenFold3Options(BaseModel):
    """OpenFold3 任务的输入声明；Launching 据此生成用户填表界面。"""

    # ---- 蛋白：三选一，必选其一 ----
    protein_sequence: str = Field(
        default="",
        title="蛋白序列（粘贴）",
        description="单条蛋白链的氨基酸序列，粘贴序列、PDB 编号、PDB 文件三选一。"
                    "支持 20 种标准氨基酸字母（ACDEFGHIKLMNPQRSTVWY），"
                    "另加 X（未知）与 U（硒代半胱氨酸）；上限 1600 个残基。",
    )
    pdb_id: str = Field(
        default="",
        title="PDB 编号",
        description="4 位 PDB 编号（如 1UBQ），运行时从 RCSB 取第一条链的序列。"
                    "三选一。与粘贴序列、PDB 文件互斥。",
        max_length=4,
    )
    pdb_file: Optional[InputFilePath] = Field(
        default=None,
        title="PDB 文件上传",
        description="PDB 结构文件，提取第一条链的序列（优先用 SEQRES，"
                    "没有时用 CA 原子）。三选一。与粘贴序列、PDB 编号互斥。",
        ftypes=["pdb", "ent"],
    )
    # ---- 配体：可选，三选一，至多一种 ----
    ligand_smiles: str = Field(
        default="",
        title="配体 SMILES",
        description="配体 SMILES，如乙醇 CCO。配体三选一，至多一种。"
                    "不填则只预测蛋白（可加 DNA/RNA）。",
    )
    ligand_sdf_file: Optional[InputFilePath] = Field(
        default=None,
        title="配体 SDF 文件上传",
        description="配体 SDF/MOL/MOL2 文件，镜像内用 OpenBabel 转成 SMILES。"
                    "配体三选一，至多一种。",
        ftypes=["sdf", "mol", "mol2"],
    )
    ligand_pubchem_cid: str = Field(
        default="",
        title="配体 PubChem 编号",
        description="配体 PubChem 编号，如乙醇 702。运行时从 PubChem 取标准 SMILES。"
                    "配体三选一，至多一种。",
    )
    # ---- 核酸：可选 ----
    dna_sequence: str = Field(
        default="",
        title="DNA 序列（可选）",
        description="DNA 序列，只接受 A/T/G/C（另加 N）；将作为 C 链参与预测。",
    )
    rna_sequence: str = Field(
        default="",
        title="RNA 序列（可选）",
        description="RNA 序列，只接受 A/U/G/C（另加 N）；将作为 D 链参与预测。",
    )
    # ---- 修饰与口袋 ----
    modifications: str = Field(
        default="",
        title="残基修饰（可选）",
        description="蛋白残基的非标准修饰，如 3:SEP,5:MHO（位置:修饰代码，"
                    "位置从 1 计数，多个用逗号分隔）。",
    )
    pocket: str = Field(
        default="",
        title="口袋约束（可选）",
        description="只用于含配体的任务：B|A:45,A:46|4.0（配体链|蛋白链:残基,…|最大距离 Å；"
                    "最大距离可省略，默认 4.0 Å）。",
    )
    # ---- MSA：可选 ----
    msa_file: Optional[InputFilePath] = Field(
        default=None,
        title="自备 MSA 文件（可选）",
        description="自备 .a3m MSA 文件。指定后跳过自动生成。第一条序列必须与输入的"
                    "蛋白序列一致。上传后与下方“生成 MSA”开关互斥。",
        ftypes=["a3m"],
    )
    generate_msa: bool = Field(
        default=True,
        title="生成 MSA",
        description="开启时通过 ColabFold 服务器自动生成 MSA（增加 2–5 分钟，"
                    "节点需能访问 api.colabfold.com）。关闭则为单序列模式，"
                    "精度可能下降；合成蛋白、从头设计蛋白建议关闭。",
    )
    use_templates: bool = Field(
        default=True,
        title="使用结构模板",
        description="开启时用 ColabFold 模板搜索结果辅助预测。关闭则不用模板，"
                    "精度可能下降。未生成 MSA 时模板搜索无效。",
    )
    # ---- 采样与输出 ----
    model_seeds: int = Field(
        default=1,
        title="模型种子数",
        description="模型种子数（1–5，默认 1）。每个种子用不同的随机初始化，"
                    "多种子可探索更多构象。",
        ge=1,
        le=5,
    )
    diffusion_samples: int = Field(
        default=5,
        title="每种子扩散样本数",
        description="每种子生成的扩散样本数（1–10，默认 5）。样本越多，"
                    "构象多样性越好，耗时也越长。",
        ge=1,
        le=10,
    )
    random_seed: Optional[int] = Field(
        default=None,
        title="随机种子（可选）",
        description="固定随机种子（非负整数）。填了之后，相同输入的预测结果可复现；"
                    "留空则每次随机。",
        ge=0,
    )
    output_format: str = Field(
        default="cif",
        title="输出结构格式",
        description="cif（含完整元数据）或 pdb（兼容旧版软件）。",
    )
    output_dir: OutputDirectory = Field(
        default="./openfold3-output",
        title="输出目录",
        description="预测结果输出目录：query.json、runner.yml、summary.csv、"
                    "predicted.cif/.pdb、report_zh.md、openfold3_raw/（原生输出）。",
    )


def _resolve_input_path(value) -> str:
    """解析 InputFilePath：优先 get_full_path()，其次 get_path()，最后 str()。"""
    if value is None:
        raise ValueError("未提供文件。")
    for method in ("get_full_path", "get_path"):
        getter = getattr(value, method, None)
        if callable(getter):
            try:
                result = getter()
            except Exception:
                continue
            if result:
                return str(result)
    if isinstance(value, (str, Path)):
        return str(value)
    return str(value)


def _resolve_output_dir(value) -> str:
    """解析 OutputDirectory：同 _resolve_input_path 的容错顺序。"""
    if value is None:
        return "./openfold3-output"
    for method in ("get_full_path", "get_path"):
        getter = getattr(value, method, None)
        if callable(getter):
            try:
                result = getter()
            except Exception:
                continue
            if result:
                return str(result)
    if isinstance(value, (str, Path)):
        return str(value)
    return str(value)


def _write_launching_report(out_dir: Path) -> None:
    """可选：在输出目录写一份 Launching 报告（.launching_report 结尾）。

    失败时只打印警告、不影响任务本身。
    """
    try:
        from dp.launching.report import Report

        title = "OpenFold3 预测完成"
        summary_path = out_dir / "summary.csv"
        if summary_path.exists():
            with open(summary_path, encoding="utf-8-sig") as fh:
                rows = list(csv.DictReader(fh))
            if rows:
                best = rows[0]
                title = ("OpenFold3 预测完成：平均 pLDDT "
                         f"{float(best['avg_plddt']):.2f}，"
                         f"pTM {float(best['ptm']):.4f}")
        report = Report(title=title, sections=[])
        report.save(str(out_dir))
    except Exception as exc:  # noqa: BLE001 - 报告是可选的，失败不阻断任务
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")


def main(opts: OpenFold3Options) -> int:
    protein_sequence = (opts.protein_sequence or "").strip()
    pdb_id = (opts.pdb_id or "").strip()
    ligand_smiles = (opts.ligand_smiles or "").strip()
    ligand_pubchem_cid = (opts.ligand_pubchem_cid or "").strip()
    dna_sequence = (opts.dna_sequence or "").strip()
    rna_sequence = (opts.rna_sequence or "").strip()
    modifications = (opts.modifications or "").strip()
    pocket = (opts.pocket or "").strip()
    output_format = (opts.output_format or "cif").strip().lower()

    # 蛋白三选一，必选其一
    protein_sources = [protein_sequence, pdb_id, opts.pdb_file]
    filled = [s for s in protein_sources if s]
    if len(filled) == 0:
        raise ValueError("蛋白输入三选一，必选其一：粘贴序列、PDB 编号、PDB 文件。")
    if len(filled) > 1:
        raise ValueError(
            "蛋白输入只能选一种：粘贴序列、PDB 编号、PDB 文件。请只填其中一项。")

    # 配体三选一，至多一种
    ligand_sources = [ligand_smiles, opts.ligand_sdf_file, ligand_pubchem_cid]
    filled_lig = [s for s in ligand_sources if s]
    if len(filled_lig) > 1:
        raise ValueError(
            "配体输入只能选一种：SMILES、SDF 文件、PubChem 编号。请只填其中一项。")
    if pocket and not filled_lig:
        raise ValueError("口袋约束需要配体：请先提供配体（SMILES、SDF 文件或 PubChem 编号）。")
    if output_format not in ("cif", "pdb"):
        raise ValueError("输出结构格式只能是 cif 或 pdb。")

    pdb_path = None
    if opts.pdb_file is not None:
        pdb_path = _resolve_input_path(opts.pdb_file)
        if not pdb_path:
            raise ValueError("上传的 PDB 文件路径解析失败，请重新上传。")
    sdf_path = None
    if opts.ligand_sdf_file is not None:
        sdf_path = _resolve_input_path(opts.ligand_sdf_file)
        if not sdf_path:
            raise ValueError("上传的 SDF 文件路径解析失败，请重新上传。")
    msa_path = None
    if opts.msa_file is not None:
        msa_path = _resolve_input_path(opts.msa_file)
        if not msa_path:
            raise ValueError("上传的 .a3m 文件路径解析失败，请重新上传。")
    if msa_path and not opts.generate_msa:
        raise ValueError(
            "不能同时上传 MSA 文件并关闭“生成 MSA”：要么上传 .a3m 供跳过自动生成，"
            "要么开启“生成 MSA”自动生成，要么只关闭开关走单序列模式。")

    out_dir = _resolve_output_dir(opts.output_dir)

    argv: list[str] = []
    if protein_sequence:
        argv += ["--protein-sequence", protein_sequence]
    if pdb_id:
        argv += ["--pdb-id", pdb_id]
    if pdb_path:
        argv += ["--pdb-file", pdb_path]
    if ligand_smiles:
        argv += ["--ligand-smiles", ligand_smiles]
    if sdf_path:
        argv += ["--ligand-sdf-file", sdf_path]
    if ligand_pubchem_cid:
        argv += ["--ligand-pubchem-cid", ligand_pubchem_cid]
    if dna_sequence:
        argv += ["--dna-sequence", dna_sequence]
    if rna_sequence:
        argv += ["--rna-sequence", rna_sequence]
    if modifications:
        argv += ["--modifications", modifications]
    if pocket:
        argv += ["--pocket", pocket]
    if msa_path:
        argv += ["--msa-file", msa_path]
    if not opts.generate_msa:
        argv += ["--no-msa"]
    if not opts.use_templates:
        argv += ["--no-templates"]
    argv += ["--model-seeds", str(opts.model_seeds)]
    argv += ["--diffusion-samples", str(opts.diffusion_samples)]
    if opts.random_seed is not None:
        argv += ["--random-seed", str(opts.random_seed)]
    argv += ["--output-format", output_format]
    argv += ["--out-dir", out_dir]

    code = run_openfold3.main(argv)
    if code != 0:
        raise RuntimeError(
            f"OpenFold3 预测失败，run_openfold3.main 返回退出码 {code}。")

    # 成功后可选写 Launching 报告（失败不阻断）
    try:
        _write_launching_report(Path(out_dir))
    except Exception as exc:  # noqa: BLE001 - 报告是可选的
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")

    return 0


def to_parser():
    return to_runner(
        OpenFold3Options,
        main,
        version="1.0.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
