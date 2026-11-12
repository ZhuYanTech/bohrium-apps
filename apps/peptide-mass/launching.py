from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    sequence_file: Optional[InputFilePath] = Field(default=None, title='蛋白质序列文件', ftypes=['fasta', 'fa', 'fas', 'faa', 'txt'])
    sequence: str = Field(default='', title='单条蛋白质序列')
    pdb_id: str = Field(default='', title='四位 PDB 编号')
    enzyme: Literal['trypsin', 'trypsin_all', 'lys_c', 'arg_c', 'asp_n', 'glu_c_phosphate', 'glu_c_bicarbonate', 'chymotrypsin', 'pepsin', 'proteinase_k', 'cnbr', 'formic_acid'] = Field(default='trypsin', title='酶切规则')
    missed: int = Field(default=0, title='最大漏切位点数')
    mass_type: Literal['mono', 'average'] = Field(default='mono', title='质量类型（mono 或 average）')
    ion: Literal['h', 'neutral', 'minus_h', '2h', '3h'] = Field(default='h', title='离子（h、neutral、minus_h、2h、3h）')
    cysteine: Literal['none', 'cam', 'cm', 'vp', 'acrylamide'] = Field(default='none', title='半胱氨酸修饰（none、cam、cm、vp、acrylamide）')
    oxidation: bool = Field(default=False, title='甲硫氨酸氧化')
    min_mass: str = Field(default='', title='最低质量或 m/z')
    max_mass: str = Field(default='', title='最高质量或 m/z')
    sort_by: Literal['position', 'mass'] = Field(default='position', title='排序（position 或 mass）')
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
