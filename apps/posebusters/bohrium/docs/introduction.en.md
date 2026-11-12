## PoseBusters docking pose validation

PoseBusters checks the chemistry and geometry of ligand poses produced by docking or structure prediction. It detects distorted bonds, intramolecular clashes, and ligand–receptor overlaps. With a crystal reference, it also checks molecular identity, stereochemistry, and root-mean-square deviation (RMSD) from the reference pose.

| Mode | Inputs | Checks |
| --- | --- | ---: |
| Molecule (mol) | Predicted pose | 12 |
| Dock (dock) | Pose and receptor | 22 |
| Redock (redock) | Pose, receptor, and crystal reference | 28 |

The Bohrium implementation selects the mode automatically. A pose that passes meets the criteria for the chosen mode. Binding affinity, activity, and the actual binding pose require independent evidence.

## Open-source repositories

- [Upstream PoseBusters (MIT)](https://github.com/maabuu/posebusters)
- [ZhuYanTech Bohrium wrapper (MIT)](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)
