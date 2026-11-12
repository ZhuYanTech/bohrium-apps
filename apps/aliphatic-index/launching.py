#!/usr/bin/env python3
"""Bohrium standard offline task entry point."""

from pathlib import Path
import sys

from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from run_aliphatic_index import write_results


class AliphaticIndexOptions(BaseModel):
    fasta: InputFilePath = Field(
        title="蛋白质 FASTA 文件",
        description="上传一条或多条蛋白质序列。每条记录需要以 > 开头的标题，只接受 20 种标准氨基酸。",
        ftypes=["fasta", "fa", "faa", "txt"],
    )
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: AliphaticIndexOptions) -> int:
    fasta = Path(options.fasta.get_full_path()).read_text(encoding="utf-8-sig")
    output = Path(options.output_dir.get_full_path())
    count = write_results(fasta, output)
    print(f"完成 {count} 条序列的脂肪族指数计算。")
    return 0


def to_parser():
    return to_runner(
        AliphaticIndexOptions,
        main,
        version="1.0.0",
        exception_handler=default_minimal_exception_handler,
    )


if __name__ == "__main__":
    to_parser()(sys.argv[1:])
