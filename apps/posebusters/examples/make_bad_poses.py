#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_bad_poses.py — 由一个合格的晶体配体，造两个一定不合格的姿势，用来验证检查确实在工作。

  bad_translated.sdf  整体平移 10 Å：离开口袋，RMSD 必然 > 2 Å
  bad_squashed.sdf    坐标整体缩到 0.5 倍：键长过短、原子互相碰撞、环被压扁

用法：python3 make_bad_poses.py <good_ligand.sdf> <输出目录>
"""
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem  # noqa: F401  （确保构象相关功能已注册）
from rdkit.Geometry import Point3D


def load_first(path: Path) -> Chem.Mol:
    mol = next(iter(Chem.SDMolSupplier(str(path), removeHs=False)), None)
    if mol is None:
        raise SystemExit(f"读不出分子：{path}")
    return mol


def transform(mol: Chem.Mol, fn) -> Chem.Mol:
    out = Chem.Mol(mol)
    conf = out.GetConformer()
    for i in range(out.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        x, y, z = fn(p.x, p.y, p.z)
        conf.SetAtomPosition(i, Point3D(x, y, z))
    return out


def write(mol: Chem.Mol, path: Path, name: str) -> None:
    mol.SetProp("_Name", name)
    w = Chem.SDWriter(str(path))
    w.write(mol)
    w.close()
    print(f"  已写出 {path}")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("用法：python3 make_bad_poses.py <good_ligand.sdf> <输出目录>")
    src, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    good = load_first(src)

    # 反例 1：整体平移 10 Å —— 跑出口袋
    write(transform(good, lambda x, y, z: (x + 10.0, y, z)),
          out_dir / "bad_translated.sdf", "BAD_TRANSLATED_10A")

    # 反例 2：坐标缩到一半 —— 键长过短、自身碰撞、环压扁
    conf = good.GetConformer()
    n = good.GetNumAtoms()
    cx = sum(conf.GetAtomPosition(i).x for i in range(n)) / n
    cy = sum(conf.GetAtomPosition(i).y for i in range(n)) / n
    cz = sum(conf.GetAtomPosition(i).z for i in range(n)) / n
    write(transform(good, lambda x, y, z: (cx + (x - cx) * 0.5,
                                           cy + (y - cy) * 0.5,
                                           cz + (z - cz) * 0.5)),
          out_dir / "bad_squashed.sdf", "BAD_SQUASHED_0.5X")
    return 0


if __name__ == "__main__":
    sys.exit(main())
