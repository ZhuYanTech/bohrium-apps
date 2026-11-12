## Choose single-file or batch input

- **Single-file run**: A predicted pose is required. Predicted poses, crystal references, and receptors accept SDF, MOL, MOL2, or PDB. For a receptor, you can also enter a four-character PDB ID. An uploaded receptor takes precedence.
- **Batch run**: Upload a ZIP containing `mol_pred/` and optional `mol_true/` and `mol_cond/` folders. Index files from 1 in ZIP entry order within each group. One reference and one receptor can be shared across all poses. To pair inputs per row, include `pairs.csv` at the ZIP root. The web pairing field is single-line, so use the ZIP for multi-line CSV. The command line accepts multi-line CSV. Use `mol_pred,mol_true,mol_cond` as column names. Reference and receptor cells can be blank.
- Receptors are kept as supplied by default. Removing a named PDB ligand or enabling automatic removal can change pocket compatibility results.

## Validation modes and outputs

Enter `auto`, `mol`, `dock`, `redock`, `regen`, or `gen`. Add `_fast` for a fast preset. The `custom` mode requires a complete JSON configuration with `modules`. Top N applies per predicted file. A `top_n` setting in the custom configuration takes precedence.

Enter `short`, `long`, or `csv` for the native report. Every run retains `results.csv`, `summary.csv`, `report_zh.md`, and metadata for the software version and resolved mode. Batch runs also have per-pair folders. Full report adds diagnostics to CSV. The summary counts passed, failed, and unevaluated checks separately. PB-valid requires every expected check to pass.

## Verification example

Use the bundled 1IA1 crystal ligand as both the prediction and reference, with the receptor file from which that ligand was removed. The redock positive control should pass **28/28** checks. RMSD thresholds apply to comparisons against a reference pose.

[Upstream open-source repository](https://github.com/maabuu/posebusters) · [Bohrium wrapper and deployment](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/posebusters)
