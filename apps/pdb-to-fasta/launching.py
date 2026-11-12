from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    structure: Optional[InputFilePath] = Field(default=None, title='PDB 或 ENT 文件', ftypes=['pdb', 'ent'])
    pdb_id: str = Field(default='', title='四位 PDB 编号')
    sequence_source: Literal['observed', 'seqres'] = Field(default='observed', title='序列来源（observed 或 seqres）')
    molecule_type: Literal['all', 'protein', 'nucleic'] = Field(default='all', title='分子类型（all、protein、nucleic）')
    chains: str = Field(default='', title='链编号（逗号分隔）')
    insert_gaps: bool = Field(default=False, title='插入编号间缺失残基')
    include_modified: bool = Field(default=True, title='包含已知修饰残基')
    header_format: Literal['id_chain', 'title_chain', 'chain'] = Field(default='id_chain', title='标题格式（id_chain、title_chain、chain）')
    wrap: int = Field(default=80, title='每行字符数（0 表示不换行）')
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: Options) -> int:
    for field in ('structure',):
        path = getattr(options, field)
        if path is not None:
            object.__setattr__(options, field, Path(path.get_full_path()))
    dest = Path(options.output_dir.get_full_path())
    dest.mkdir(parents=True, exist_ok=True)
    run(options, dest)
    return 0


if __name__ == "__main__":
    to_runner(Options, main, version="1.0.0", exception_handler=default_minimal_exception_handler)(sys.argv[1:])
