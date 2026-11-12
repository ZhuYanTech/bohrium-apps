from pathlib import Path
import sys
from typing import Literal, Optional
from dp.launching.cli import default_minimal_exception_handler, to_runner
from dp.launching.typing import BaseModel, Field, InputFilePath, OutputDirectory

from tool import run


class Options(BaseModel):
    molecule_file: Optional[InputFilePath] = Field(default=None, title='分子或结构文件', ftypes=['smi', 'smiles', 'txt', 'inchi', 'mol', 'sdf', 'mol2', 'pdb', 'pdbqt', 'xyz', 'cif', 'can', 'cml', 'cdx'])
    molecule_text: str = Field(default='', title='分子文本')
    input_format: Literal['auto', 'smi', 'can', 'mol', 'sdf', 'mol2', 'pdb', 'pdbqt', 'xyz', 'cif', 'inchi', 'cml', 'cdx', 'fasta'] = Field(default='auto', title='输入格式（auto 或 Open Babel 格式代码）')
    output_format: Literal['smi', 'can', 'mol', 'sdf', 'mol2', 'pdb', 'pdbqt', 'xyz', 'cif', 'inchi', 'cml', 'fasta', 'molreport'] = Field(default='mol', title='输出格式')
    coordinates: Literal['none', '2d', '3d'] = Field(default='none', title='坐标（none、2d、3d）')
    hydrogens: Literal['none', 'add', 'polar', 'nonpolar', 'delete', 'delete_nonpolar'] = Field(default='none', title='氢原子处理')
    ph: str = Field(default='', title='pH（留空禁用）')
    charges: Literal['none', 'gasteiger'] = Field(default='none', title='电荷（none 或 gasteiger）')
    force_field: Literal['none', 'MMFF94', 'MMFF94s', 'UFF', 'GAFF', 'Ghemical'] = Field(default='none', title='最小化力场（none 或力场名称）')
    minimization_steps: int = Field(default=250, ge=1, le=5000, title="最小化步数")
    output_dir: OutputDirectory = Field(default="./output", title="输出目录")


def main(options: Options) -> int:
    for field in ('molecule_file',):
        path = getattr(options, field)
        if path is not None:
            object.__setattr__(options, field, Path(path.get_full_path()))
    dest = Path(options.output_dir.get_full_path())
    dest.mkdir(parents=True, exist_ok=True)
    run(options, dest)
    return 0


if __name__ == "__main__":
    to_runner(Options, main, version="1.0.0", exception_handler=default_minimal_exception_handler)(sys.argv[1:])
