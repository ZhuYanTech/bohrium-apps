#!/usr/bin/env python3
"""Bohrium standard offline task entry point."""

from pathlib import Path
import sys

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from run_aliphatic_index import fetch_fasta, write_results


class AliphaticIndexOptions(BaseModel):
    fasta: InputFilePath | None = Field(
        default=None,
        title="蛋白质序列或结构文件",
        description="支持 FASTA、TXT、CSV 和 PDB。请在文件、粘贴序列或 PDB 编号中选择一个。",
        ftypes=["fasta", "fa", "fas", "faa", "txt", "csv", "pdb"],
    )
    sequence: str = Field(default="", title="粘贴蛋白质序列", description="单条序列或带标题的多条 FASTA。")
    pdb_id: str = Field(default="", title="RCSB PDB 编号", max_length=4)
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: AliphaticIndexOptions) -> int:
    sequence, pdb_id = options.sequence.strip(), options.pdb_id.strip()
    if sum(bool(value) for value in (options.fasta, sequence, pdb_id)) != 1:
        raise ValueError("请在文件、粘贴序列和 PDB 编号中选择一个输入。")
    output = Path(options.output_dir.get_full_path())
    if options.fasta:
        path = Path(options.fasta.get_full_path())
        count = write_results(path.read_text(encoding="utf-8-sig"), output,
                              path.suffix.lower()[1:], path.stem)
    else:
        count = write_results(sequence or fetch_fasta(pdb_id), output)
    print(f"完成 {count} 条序列的脂肪族指数计算。")
    return 0


def to_parser():
    return to_runner(
        AliphaticIndexOptions, main, version="1.1.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
