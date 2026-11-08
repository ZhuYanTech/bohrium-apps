#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launching.py — Boltz-2 玻尔 App 的 DP-Launching 入口（标准离线任务型）

玻尔开发者中心创建 App 时选“标准离线任务”，新建版本时 EntryPoint 填
镜像里的绝对路径：/app/launching.py。

作用：把 run_boltz2.py 的命令行封装成 Launching 声明式入口。
Launching 在建版本时按 Boltz2Options 的声明自动生成 JSON Schema，
展开成用户填表界面（蛋白序列 / 配体 SMILES / MSA / 采样参数），
再把用户填的参数以命令行参数形式传回本文件，main() 转调 run_boltz2.main()。

引用：
- Passaro, S. et al. Boltz-2: Towards Accurate and Efficient Binding Affinity
  Prediction. bioRxiv (2025). doi:10.1101/2025.06.14.659707
- Boltz-2 许可：MIT。

本文件不调用任何第三方 API、不含密钥；唯一的网络访问是 run_boltz2.py
默认用公开 ColabFold 服务器自动生成 MSA（可在表单里关掉，改传 .a3m）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# 让 run_boltz2.py 能从同目录导入（无论从哪里启动本文件）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import (
    BaseModel,
    Field,
    InputFilePath,
    OutputDirectory,
)

import run_boltz2  # noqa: E402  (在 sys.path 调整之后导入)


class Boltz2Options(BaseModel):
    """Boltz-2 任务的输入声明；Launching 据此生成用户填表界面。"""

    protein_sequence: str = Field(
        default="",
        title="蛋白氨基酸序列",
        description="单条链，粘贴序列或 FASTA 文本；≤2900 个残基，超过 1500 个需更大显存机型",
    )
    ligand_smiles: str = Field(
        default="",
        title="配体 SMILES",
        description="与 CCD 编号二选一，优先用 SMILES",
    )
    ligand_ccd: str = Field(
        default="",
        title="或配体 CCD 编号",
        description="如 ATP；与 SMILES 二选一，优先用 SMILES",
    )
    msa_file: Optional[InputFilePath] = Field(
        default=None,
        title="上传 .a3m MSA 文件（可选）",
        description="指定后跳过自动生成；第一条序列须与输入蛋白序列一致",
        ftypes=["a3m"],
    )
    no_msa: bool = Field(
        default=False,
        title="不使用 MSA（单序列模式）",
        description="精度可能下降；只在自动生成失败时用",
    )
    output_format: str = Field(
        default="pdb",
        title="输出结构格式",
        description="pdb 或 mmcif，默认 pdb（便于后续接 PLIP 分析）",
    )
    diffusion_samples: int = Field(
        default=1,
        title="结构样本数",
        description="默认 1；要比较多个样本时可提到 3–5",
        ge=1,
        le=20,
    )
    recycling_steps: int = Field(
        default=3,
        title="循环精修次数",
        description="默认 3",
        ge=1,
        le=10,
    )
    sampling_steps: int = Field(
        default=200,
        title="结构采样步数",
        description="默认 200",
        ge=50,
        le=500,
    )
    dry_run: bool = Field(
        default=False,
        title="仅生成输入文件，不实际预测",
        description="测试用：只验证输入并生成 input.yaml",
    )
    output_dir: OutputDirectory = Field(
        default="./output",
        title="输出目录",
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
        return "./output"
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


def _write_launching_report(out_dir: Path, affinity: dict | None) -> None:
    """可选：在输出目录写一份 Launching 报告（.launching_report 结尾）。

    失败时只打印警告、不影响任务本身。
    """
    try:
        from dp.launching.report import Report

        if affinity is not None:
            title = ("Boltz-2 预测完成：结合概率 "
                     f"{affinity['affinity_probability_binary']:.3f}，"
                     "预测 log10(IC50) "
                     f"{affinity['affinity_pred_value']:.3f}")
        else:
            title = "Boltz-2 预测完成"
        report = Report(title=title, sections=[])
        report.save(str(out_dir))
    except Exception as exc:  # noqa: BLE001 - 报告是可选的，失败不阻断任务
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")


def main(opts: Boltz2Options) -> int:
    sequence = (opts.protein_sequence or "").strip()
    if not sequence:
        raise ValueError("请填写蛋白氨基酸序列。")
    smiles = (opts.ligand_smiles or "").strip()
    ccd = (opts.ligand_ccd or "").strip()
    if smiles and ccd:
        print("提示：同时提供了 SMILES 和 CCD 编号，优先使用 SMILES。")
        ccd = ""
    if not smiles and not ccd:
        raise ValueError("请填写配体 SMILES，或填写配体 CCD 编号（二选一）。")
    output_format = (opts.output_format or "pdb").strip().lower()
    if output_format not in ("pdb", "mmcif"):
        raise ValueError("输出结构格式只能是 pdb 或 mmcif。")

    msa_path = None
    if opts.msa_file is not None:
        msa_path = _resolve_input_path(opts.msa_file)
        if not msa_path:
            raise ValueError("上传的 .a3m 文件路径解析失败，请重新上传。")
    if msa_path and opts.no_msa:
        raise ValueError("不能同时上传 .a3m 又勾选“不使用 MSA”。")

    out_dir = _resolve_output_dir(opts.output_dir)

    argv: list[str] = [
        "--sequence", sequence,
        "--out-dir", out_dir,
        "--output-format", output_format,
        "--diffusion-samples", str(opts.diffusion_samples),
        "--recycling-steps", str(opts.recycling_steps),
        "--sampling-steps", str(opts.sampling_steps),
    ]
    if smiles:
        argv += ["--ligand-smiles", smiles]
    else:
        argv += ["--ligand-ccd", ccd]
    if msa_path is not None:
        argv += ["--msa-file", msa_path]
    if opts.no_msa:
        argv += ["--no-msa"]
    if opts.dry_run:
        argv += ["--dry-run"]

    code = run_boltz2.main(argv)
    if code != 0:
        raise RuntimeError(f"Boltz-2 预测失败，run_boltz2.main 返回退出码 {code}。")

    # 成功后可选写 Launching 报告（失败不阻断）
    try:
        affinity = None
        affinity_path = Path(out_dir) / "affinity.json"
        if affinity_path.exists():
            affinity = json.loads(affinity_path.read_text(encoding="utf-8"))
        _write_launching_report(Path(out_dir), affinity)
    except Exception as exc:  # noqa: BLE001 - 报告是可选的
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")

    return 0


def to_parser():
    return to_runner(
        Boltz2Options,
        main,
        version="1.0.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
