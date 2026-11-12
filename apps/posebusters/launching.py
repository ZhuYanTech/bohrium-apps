#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launching.py — PoseBusters 玻尔 App 的 DP-Launching 入口（标准离线任务型）

玻尔开发者中心创建 App 时选"标准离线任务"，新建版本时 EntryPoint 填
镜像里的绝对路径：/app/launching.py。

作用：把 run_posebusters.py 的命令行封装成 Launching 声明式入口。
Launching 在建版本时按 PoseBustersOptions 的声明自动生成 JSON Schema，
展开成用户填表界面，再把用户填的参数以命令行参数形式传回本文件，
main() 转调 run_posebusters.main()。

引用：
- Buttenschoen, M., Morris, G. M., Deane, C. M. PoseBusters: AI-based docking
  methods fail to generate physically valid poses or generalise to novel sequences.
  Chem. Sci. 15, 3130-3139 (2024). doi:10.1039/D3SC04185A
- PoseBusters 许可：MIT。

本文件不调用任何第三方 API、不含密钥；唯一的网络访问是 run_posebusters.py
按用户给的 PDB 编号从 RCSB 下载蛋白结构。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional

# 让 run_posebusters.py 能从同目录导入（无论从哪里启动本文件）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import (
    BaseModel,
    Field,
    InputFilePath,
    OutputDirectory,
)

import run_posebusters  # noqa: E402  （在 sys.path 调整之后导入）


class PoseBustersOptions(BaseModel):
    """PoseBusters 任务的输入声明；Launching 据此生成用户填表界面。"""

    mol_pred: InputFilePath = Field(
        title="待检查的配体姿势",
        description="对接或结构预测产生的配体姿势文件（SDF/MOL/MOL2/PDB）。"
                    "一个文件里可以放多个分子或多个构象，会逐个检查",
        ftypes=["sdf", "mol", "mol2", "pdb"],
    )
    protein_file: Optional[InputFilePath] = Field(
        default=None,
        title="蛋白结构（可选）",
        description="受体蛋白结构（PDB）。给了就增加「与口袋的相容性」检查："
                    "原子碰撞、体积穿模、配体是否跑出口袋",
        ftypes=["pdb"],
    )
    pdb_id: Optional[str] = Field(
        default="",
        title="或输入蛋白的 PDB 编号（可选）",
        description="4 位编号，如 1IA1，自动从 RCSB 下载。与上传蛋白文件二选一",
        max_length=4,
    )
    mol_true: Optional[InputFilePath] = Field(
        default=None,
        title="晶体参考配体（可选）",
        description="已知的晶体配体姿势（SDF）。给了就增加「与参考一致」和"
                    "「RMSD ≤ 2 Å」检查，用于回顾性评估对接准确度",
        ftypes=["sdf", "mol"],
    )
    strip_ligand: Optional[str] = Field(
        default="",
        title="从蛋白中删除的配体残基名（可选）",
        description="如 TQ3，多个用逗号分隔。蛋白结构里若还留着要对接的那个配体，"
                    "它会和自己碰撞导致结果全错。留空时会尝试从姿势文件的分子名自动推断",
        max_length=64,
    )
    full_report: bool = Field(
        default=False,
        title="明细表附带具体数值",
        description="在 results.csv 里附上每项检查的具体数值，而不只是通过/未通过",
    )
    output_dir: OutputDirectory = Field(
        default="./output",
        title="输出目录",
    )


def _resolve_path(value, default: str = "") -> str:
    """解析 InputFilePath / OutputDirectory：

    API 不确定性：官方文档示例里 get_path() 和 get_full_path() 都出现过，
    未说明哪个是标准入口；这里按 get_full_path -> get_path -> str 的顺序
    取第一个能用的非空结果。
    """
    if value is None:
        return default
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


def _write_launching_report(out_dir: Path, total: int, valid: int) -> None:
    """可选：在输出目录写一份 Launching 报告。失败只告警，不影响任务本身。"""
    try:
        from dp.launching.report import Report

        Report(
            title=f"PoseBusters 姿势检查：{total} 个姿势，{valid} 个通过全部检查",
            sections=[],
        ).save(str(out_dir))
    except Exception as exc:  # noqa: BLE001 - 报告是可选的，失败不阻断任务
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")


def main(opts: PoseBustersOptions) -> int:
    mol_pred = _resolve_path(opts.mol_pred)
    if not mol_pred:
        raise ValueError("请上传待检查的配体姿势文件。")

    out_dir = _resolve_path(opts.output_dir, "./output")
    argv: list[str] = ["--mol-pred", mol_pred, "--out-dir", out_dir]

    protein = _resolve_path(opts.protein_file)
    pdb_id = (opts.pdb_id or "").strip()
    if protein:
        argv += ["--protein", protein]
        if pdb_id:
            print("提示：同时提供了蛋白文件和 PDB 编号，优先使用上传的文件。")
    elif pdb_id:
        argv += ["--pdb-id", pdb_id.upper()]

    mol_true = _resolve_path(opts.mol_true)
    if mol_true:
        argv += ["--mol-true", mol_true]

    if (opts.strip_ligand or "").strip():
        argv += ["--strip-ligand", opts.strip_ligand.strip()]
    if opts.full_report:
        argv += ["--full-report"]

    code = run_posebusters.main(argv)
    if code != 0:
        raise RuntimeError(f"PoseBusters 检查失败，run_posebusters.main 返回退出码 {code}。")

    # 成功后可选写 Launching 报告（失败不阻断）
    try:
        summary_path = Path(out_dir) / "summary.csv"
        total = valid = 0
        if summary_path.exists():
            with open(summary_path, encoding="utf-8-sig") as fh:
                for row in csv.DictReader(fh):
                    total += 1
                    if row.get("PB_valid") == "是":
                        valid += 1
        _write_launching_report(Path(out_dir), total, valid)
    except Exception as exc:  # noqa: BLE001 - 报告是可选的
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")

    return 0


def to_parser():
    return to_runner(
        PoseBustersOptions,
        main,
        version="1.0.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
