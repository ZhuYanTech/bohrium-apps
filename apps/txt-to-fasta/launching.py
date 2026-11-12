from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    text_file: Optional[InputFilePath] = Field(default=None, title='文本文件', ftypes=['fasta', 'fa', 'fas', 'faa', 'txt', 'csv', 'tsv', 'seq'])
    sequence: str = Field(default='', title='单行文本')
    multi: Literal['auto', 'blank', 'join', 'custom'] = Field(default='auto', title='分组方式（auto、blank、join、custom）')
    separator: str = Field(default='', title='自定义分隔符')
    sequence_type: Literal['auto', 'dna', 'rna', 'nucleotide', 'protein'] = Field(default='auto', title='序列类型（auto、dna、rna、nucleotide、protein）')
    names: Literal['input', 'numbered'] = Field(default='input', title='标题（input 或 numbered）')
    wrap: int = Field(default=0, title='每行字符数（0 表示不换行）')
    letter_case: Literal['upper', 'lower', 'original'] = Field(default='upper', title='字母大小写（upper、lower、original）')
    validation: Literal['lenient', 'strict', 'off'] = Field(default='lenient', title='校验（lenient、strict、off）')
    keep_gaps: bool = Field(default=False, title='保留缺口')
    keep_stops: bool = Field(default=False, title='保留终止符')
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: Options) -> int:
    for field in ('text_file',):
        path = getattr(options, field)
        if path is not None:
            object.__setattr__(options, field, Path(path.get_full_path()))
    dest = Path(options.output_dir.get_full_path())
    dest.mkdir(parents=True, exist_ok=True)
    run(options, dest)
    return 0


if __name__ == "__main__":
    to_runner(Options, main, version="1.0.0", exception_handler=default_minimal_exception_handler)(sys.argv[1:])
