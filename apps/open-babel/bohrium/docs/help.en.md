## Inputs, settings and outputs

Upload one file or paste one molecule string. Use a file for multiple molecules. Input auto-detection and mol output are defaults. Common format codes include smi, can, sdf, mol, mol2, pdb, pdbqt, xyz, cif, inchi, and cml. Coordinate options are none, 2d, and 3d. Hydrogen options are none, add, polar, nonpolar, delete, and delete_nonpolar. Leave pH blank to disable correction. Charges can be gasteiger. Force fields include MMFF94, MMFF94s, UFF, GAFF, and Ghemical. Minimization uses 250 steps by default and accepts 1 to 5,000. Download converted.<format> and run.log. CCO produces a MOL file with three heavy atoms.

Input files are limited to 10 MiB and conversion times out after 120 seconds. Auto-detection uses a recognized extension before inspecting the content. Force-field minimization requires 3D coordinates. Check the log for the actual arguments, warnings, and molecule count. A two-line SMILES file with `sdf`, `2d`, and `add` yields two records with explicit hydrogens.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/open-babel) · [Upstream repository](https://github.com/openbabel/openbabel)
