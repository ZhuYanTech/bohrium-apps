#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launching.py — PLIP 玻尔 App 的 DP-Launching 入口（标准离线任务型）

玻尔开发者中心创建 App 时选“标准离线任务”，新建版本时 EntryPoint 填
镜像里的绝对路径：/app/launching.py。

作用：把 run_plip.py 的命令行封装成 Launching 声明式入口。
Launching 在建版本时按 PlipOptions 的声明自动生成 JSON Schema，
展开成用户填表界面（上传 PDB / 输入 PDB 编号 / 模型编号 / 配体过滤），
再把用户填的参数以命令行参数形式传回本文件，main() 转调 run_plip.main()。

引用：
- Salentin, S. et al. PLIP: fully automated protein-ligand interaction profiler.
  Nucleic Acids Res. 43 (W1), W443-W447 (2015). doi:10.1093/nar/gkv315
- Schake, P., Bolz, S. N. et al. PLIP 2025. Nucleic Acids Res. (2025), gkaf361.
- PLIP 许可：GNU GPLv2。

本文件不调用任何第三方 API、不含密钥；唯一的网络访问是 run_plip.py
按用户给的 PDB 编号从 RCSB 下载 PDB 文件。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional

# 让 run_plip.py 能从同目录导入（无论从哪里启动本文件）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import (
    BaseModel,
    Field,
    InputFilePath,
    OutputDirectory,
)

import run_plip  # noqa: E402  (在 sys.path 调整之后导入)


class PlipOptions(BaseModel):
    """PLIP 任务的输入声明；Launching 据此生成用户填表界面。"""

    pdb_file: Optional[InputFilePath] = Field(
        default=None,
        title="上传 PDB 文件",
        description="蛋白-配体复合物结构，须含 HETATM 配体记录",
        ftypes=["pdb", "ent"],
    )
    pdb_id: Optional[str] = Field(
        default="",
        title="或输入 PDB 编号",
        description="4 位编号，从 RCSB 下载；与上传文件二选一，优先用上传文件",
        max_length=4,
    )
    model: int = Field(
        default=1,
        title="模型编号",
        description="多模型 PDB 时选第几个模型",
        ge=1,
    )
    ligand: str = Field(
        default="",
        title="只分析指定配体",
        description="如 JQ1，留空分析全部配体",
    )
    exclude_solvents: bool = Field(
        default=False,
        title="过滤结晶溶剂",
        description="过滤 DMS、EDO 等常见结晶溶剂/添加剂",
    )
    output_dir: OutputDirectory = Field(
        default="./output",
        title="输出目录",
    )


def _resolve_input_path(value) -> str:
    """解析 InputFilePath：优先 get_full_path()，其次 get_path()，最后 str()。

    API 不确定性：Feishu 文档示例用 get_path()/get_full_path()，未说明
    哪个是标准入口；这里两个都试，按 get_full_path -> get_path -> str 的
    顺序取第一个能用的非空结果。
    """
    if value is None:
        raise ValueError("未提供 PDB 文件。")
    for method in ("get_full_path", "get_path"):
        getter = getattr(value, method, None)
        if callable(getter):
            try:
                result = getter()
            except Exception:
                continue
            if result:
                return str(result)
    # InputFilePath 也可能是 str / Path 的子类
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


def _write_launching_report(out_dir: Path, total: int, source_desc: str) -> None:
    """可选：在输出目录写一份 Launching 报告（.launching_report 结尾）。

    失败时只打印警告、不影响任务本身：Report 的 section 格式在官方文档
    里未完全钉死，本地也没有 dp.launching 可调试预览。
    """
    try:
        from dp.launching.report import Report

        report = Report(
            title=f"PLIP 相互作用分析报告（共 {total} 个相互作用）",
            sections=[],
        )
        report.save(str(out_dir))
    except Exception as exc:  # noqa: BLE001 - 报告是可选的，失败不阻断任务
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")


def main(opts: PlipOptions) -> int:
    has_file = opts.pdb_file is not None
    pdb_id = (opts.pdb_id or "").strip()
    if has_file and pdb_id:
        # 按字段说明：同时给了文件和编号时优先用上传的文件
        print("提示：同时提供了 PDB 文件和 PDB 编号，优先使用上传的文件。")
        pdb_id = ""
    if not has_file and not pdb_id:
        raise ValueError("请上传一个 PDB 文件，或输入一个 PDB 编号（二选一）。")
    if has_file and not pdb_id:
        pdb_path = _resolve_input_path(opts.pdb_file)
        if not pdb_path:
            raise ValueError("上传的 PDB 文件路径解析失败，请重新上传。")
    else:
        pdb_path = None

    out_dir = _resolve_output_dir(opts.output_dir)

    argv: list[str] = ["--out-dir", out_dir, "--model", str(opts.model)]
    if pdb_path is not None:
        argv += ["--pdb-file", pdb_path]
        source_desc = f"本地文件 {pdb_path}"
    else:
        argv += ["--pdb-id", pdb_id.upper()]
        source_desc = f"PDB ID {pdb_id.upper()}（从 RCSB 下载）"

    if (opts.ligand or "").strip():
        argv += ["--ligand", opts.ligand.strip()]
    if opts.exclude_solvents:
        argv += ["--exclude-solvents"]

    code = run_plip.main(argv)
    if code != 0:
        raise RuntimeError(f"PLIP 分析失败，run_plip.main 返回退出码 {code}。")

    # 成功后可选写 Launching 报告（失败不阻断）
    try:
        csv_path = Path(out_dir) / "interactions.csv"
        total = 0
        if csv_path.exists():
            with open(csv_path, encoding="utf-8-sig") as fh:
                total = sum(1 for _ in csv.DictReader(fh))
        _write_launching_report(Path(out_dir), total, source_desc)
    except Exception as exc:  # noqa: BLE001 - 报告是可选的
        print(f"警告：生成 Launching 报告失败（已跳过，不影响结果）：{exc}")

    return 0


def to_parser():
    return to_runner(
        PlipOptions,
        main,
        version="1.0.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
