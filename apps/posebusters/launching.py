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
from tempfile import TemporaryDirectory
from typing import Literal
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

import run_posebusters
from batch_inputs import load_bundle


class PoseBustersOptions(BaseModel):
    """PoseBusters 任务的输入声明；Launching 据此生成用户填表界面。"""

    mol_pred: Optional[InputFilePath] = Field(
        default=None,
        title="待检查的配体姿势",
        description="对接或结构预测产生的配体姿势文件（SDF/MOL/MOL2/PDB）。"
                    "一个文件里可以放多个分子或多个构象，会逐个检查",
        ftypes=["sdf", "mol", "mol2", "pdb"],
    )
    protein_file: Optional[InputFilePath] = Field(
        default=None,
        title="蛋白结构（可选）",
        description="受体结构（PDB/SDF/MOL/MOL2）。给了就增加「与口袋的相容性」检查："
                    "原子碰撞、体积穿模、配体是否跑出口袋",
        ftypes=["pdb", "sdf", "mol", "mol2"],
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
        description="已知的晶体配体姿势（SDF/MOL/MOL2/PDB）。给了就增加「与参考一致」和"
                    "「RMSD ≤ 2 Å」检查，用于回顾性评估对接准确度",
        ftypes=["sdf", "mol", "mol2", "pdb"],
    )
    strip_ligand: Optional[str] = Field(
        default="",
        title="从蛋白中删除的配体残基名（可选）",
        description="如 TQ3，多个用逗号分隔。蛋白结构里若还留着要对接的那个配体，"
                    "它会和自己碰撞导致结果全错。只对 PDB 生效，默认保留受体原样",
        max_length=64,
    )
    full_report: bool = Field(
        default=False,
        title="明细表附带具体数值",
        description="在 results.csv 里附上每项检查的具体数值，而不只是通过/未通过",
    )
    bundle: Optional[InputFilePath] = Field(default=None, title="批量输入 ZIP", ftypes=["zip"],
        description="mol_pred/ 必填，mol_true/ 和 mol_cond/ 可选。组内按 ZIP 文件顺序编号，可包含 pairs.csv。")
    pairing: str = Field(default="", title="粘贴 CSV 配对表",
        description="仅用于批量 ZIP，列为 mol_pred、mol_true、mol_cond，编号从 1 开始。")
    validation_mode: Literal["auto", "mol", "dock", "redock", "regen", "gen",
                             "mol_fast", "dock_fast", "redock_fast", "regen_fast", "gen_fast", "custom"] = Field(
        default="auto", title="验证模式")
    output_format: Literal["short", "long", "csv"] = Field(default="short", title="原生报告格式")
    top_n: Optional[int] = Field(default=None, ge=1, title="每个预测文件最多检查前 N 个姿势")
    config_json: Optional[InputFilePath] = Field(default=None, title="自定义 JSON 配置", ftypes=["json"])
    auto_strip: bool = Field(default=False, title="自动识别并移除 PDB 中的同名配体")
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
    out_dir = Path(_resolve_path(opts.output_dir, "./output"))
    mol_pred = _resolve_path(opts.mol_pred)
    bundle = _resolve_path(opts.bundle)
    if bool(mol_pred) == bool(bundle):
        raise ValueError("请在单个待检查姿势文件和批量 ZIP 中选择一个。")
    if opts.pairing.strip() and not bundle:
        raise ValueError("CSV 配对表仅用于批量 ZIP。")

    protein = _resolve_path(opts.protein_file)
    reference = _resolve_path(opts.mol_true)
    pdb_id = (opts.pdb_id or "").strip()
    if bundle and (protein or reference or pdb_id):
        raise ValueError("使用 ZIP 时，请将参考和受体放入压缩包。")
    common = ["--validation-mode", opts.validation_mode, "--output-format", opts.output_format]
    for flag, value in (
        ("--config-json", _resolve_path(opts.config_json)),
        ("--top-n", opts.top_n),
        ("--strip-ligand", (opts.strip_ligand or "").strip()),
    ):
        if value:
            common += [flag, str(value)]
    if opts.full_report:
        common.append("--full-report")
    if not opts.auto_strip and not opts.strip_ligand:
        common.append("--no-auto-strip")

    if bundle:
        out_dir.mkdir(parents=True, exist_ok=True)
        batch_rows = []
        with TemporaryDirectory() as temporary:
            pairs = load_bundle(Path(bundle), Path(temporary), opts.pairing)
            for index, pair in enumerate(pairs, 1):
                dest = out_dir / f"pair_{index:03d}"
                argv = common + ["--out-dir", str(dest)]
                for field, flag in (("mol_pred", "--mol-pred"), ("mol_true", "--mol-true"), ("mol_cond", "--protein")):
                    if field in pair:
                        argv += [flag, str(pair[field])]
                run_posebusters.main(argv)
                with (dest / "summary.csv").open(encoding="utf-8-sig") as handle:
                    batch_rows.extend({"配对编号": index, **row} for row in csv.DictReader(handle))
        with (out_dir / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(batch_rows[0]))
            writer.writeheader()
            writer.writerows(batch_rows)
    else:
        argv = common + ["--mol-pred", mol_pred, "--out-dir", str(out_dir)]
        for flag, value in (("--protein", protein), ("--pdb-id", pdb_id), ("--mol-true", reference)):
            if value:
                argv += [flag, value]
        run_posebusters.main(argv)

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
        version="1.1.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
