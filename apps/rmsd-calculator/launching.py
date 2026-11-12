from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    reference: Optional[InputFilePath] = Field(default=None, title='参考结构', ftypes=['pdb', 'ent', 'cif', 'mmcif', 'pdbx'])
    comparison: Optional[InputFilePath] = Field(default=None, title='待比较结构或 ZIP', ftypes=['pdb', 'ent', 'cif', 'mmcif', 'pdbx', 'zip'])
    reference_id: str = Field(default='', title='参考 PDB 编号')
    comparison_id: str = Field(default='', title='待比较 PDB 编号')
    atoms: Literal['ca', 'backbone', 'protein', 'heavy', 'all'] = Field(default='ca', title='测量原子（ca、backbone、protein、heavy、all）')
    fit_atoms: Literal['same', 'ca', 'backbone', 'protein', 'heavy', 'all'] = Field(default='same', title='拟合原子（same 或选择码）')
    compare_by: Literal['structure', 'chain', 'mapped'] = Field(default='structure', title='比较方式（structure、chain、mapped）')
    chain_mapping: str = Field(default='', title='链映射，例如 A:X,B:Y')
    weighting: Literal['uniform', 'mass'] = Field(default='uniform', title='加权方式（uniform、mass）')
    models: Literal['first', 'all'] = Field(default='first', title='模型（first 或 all）')
    fit_range: str = Field(default='', title='拟合残基编号范围')
    measure_range: str = Field(default='', title='测量残基编号范围')
    align: bool = Field(default=True, title='自动刚体拟合')
    fitted: bool = Field(default=True, title='返回拟合结构')
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: Options) -> int:
    for field in ('reference', 'comparison'):
        path = getattr(options, field)
        if path is not None:
            object.__setattr__(options, field, Path(path.get_full_path()))
    dest = Path(options.output_dir.get_full_path())
    dest.mkdir(parents=True, exist_ok=True)
    run(options, dest)
    return 0


if __name__ == "__main__":
    to_runner(Options, main, version="1.0.0", exception_handler=default_minimal_exception_handler)(sys.argv[1:])
