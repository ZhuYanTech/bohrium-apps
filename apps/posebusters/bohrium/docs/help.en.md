## Prepare the inputs

- **Predicted pose (required):** Upload SDF, MOL, MOL2, or PDB. For several poses sharing a receptor, use a multi-record SDF file.
- **Receptor (optional):** Upload PDB, CIF, or ENT, or enter a four-character PDB ID. An uploaded receptor takes precedence.
- **Crystal reference (optional):** Upload SDF or MOL. Redock checks also require a receptor.
- **Ligand residue names to remove (optional):** Enter comma-separated residue names. A copy of the evaluated ligand in the receptor can cause self-overlap. Keep waters and cofactors for the corresponding checks.

## Run the calculation and read the output

Upload the files, select a CPU machine, and submit. Enable the full report option when you need numeric diagnostics.

- `summary.csv`: Pass counts, failed checks, and overall PoseBusters validity (PB-valid) for each pose.
- `results.csv`: Detailed results by check.
- `report_zh.md`: Chinese report. `posebusters_raw/` contains raw results and receptor files generated during the run.

## Reproduce the benchmark

Use the bundled PoseBusters 1IA1 benchmark. Supply the crystal ligand as both the predicted pose and the reference, together with the receptor file from which that ligand was removed. This positive control should pass all **28** redock checks. The RMSD ≤ 2 Å criterion applies to comparisons with a reference pose.

[Open-source implementation, examples, and deployment guide](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)
