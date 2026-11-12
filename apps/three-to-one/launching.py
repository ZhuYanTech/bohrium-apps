from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    text_file: Optional[InputFilePath] = Field(default=None, title='三字母序列文件', ftypes=['fasta', 'fa', 'fas', 'faa', 'txt', 'seq'])
    sequence: str = Field(default='', title='单行三字母序列')
    delimiter: Literal['auto', 'hyphen', 'space', 'comma', 'tab', 'semicolon', 'custom'] = Field(default='auto', title='分隔符（auto、hyphen、space、comma、tab、semicolon、custom）')
    custom_delimiter: str = Field(default='/', title='自定义分隔符')
    unknown: Literal['x', 'skip', 'error', 'bracket'] = Field(default='x', title='未知残基（x、skip、error、bracket）')
    letter_case: Literal['upper', 'lower'] = Field(default='upper', title='输出大小写（upper、lower）')
    preserve_fasta: bool = Field(default=True, title='保留 FASTA 标题')
    wrap: int = Field(default=0, title='每行字符数')
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
