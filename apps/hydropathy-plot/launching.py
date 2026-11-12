from pathlib import Path
import sys
from typing import Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    sequence_file: Optional[InputFilePath] = Field(default=None, title='序列文件或 PDB', ftypes=['fasta', 'fa', 'fas', 'faa', 'txt', 'pdb', 'ent'])
    sequence: str = Field(default='', title='单条蛋白质序列')
    pdb_id: str = Field(default='', title='四位 PDB 编号')
    window: int = Field(default=9, title='滑动窗口（5 到 21 的奇数）')
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: Options) -> int:
    for field in ('sequence_file',):
        path = getattr(options, field)
        if path is not None:
            object.__setattr__(options, field, Path(path.get_full_path()))
    dest = Path(options.output_dir.get_full_path())
    dest.mkdir(parents=True, exist_ok=True)
    run(options, dest)
    return 0


if __name__ == "__main__":
    to_runner(Options, main, version="1.0.0", exception_handler=default_minimal_exception_handler)(sys.argv[1:])
