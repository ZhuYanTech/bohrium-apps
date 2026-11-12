## Inputs, settings and outputs

Upload reference and comparison PDB/mmCIF files, or use PDB IDs. A comparison ZIP holds multiple structures. Defaults are Cα, uniform weighting, the first model, and Kabsch fitting. Set separate fit and measurement atom types and residue ranges, and compare structures, chains, or explicit chain mappings. Atoms match by identifiers. Outputs include global and residue CSVs, transformations JSON, and optional fitted structures. Comparing 1UBQ to itself gives Cα RMSD near 0 Å.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/rmsd-calculator) · [Upstream repository](https://github.com/biopython/biopython)
