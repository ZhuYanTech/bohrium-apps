## Inputs, settings and outputs

Upload SMI, SMILES, TXT, CSV, or TSV, or paste one SMILES. CSV/TSV may use smiles and name/id columns. The limits are 500 Da, 5, 5, and 10. A compound passes with zero or one violation. Invalid SMILES are marked individually. Aspirin gives 180.16 Da, LogP 1.31, one donor, and three acceptors. The screen does not replace absorption measurements.

`lipinski.csv` retains the name and SMILES and reports all four calculated properties, violation count, decision, and parsing status. The thresholds are 500 Da for molecular weight, 5 for LogP, 5 donors, and 10 acceptors. Invalid rows remain in batch results with their parsing status.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/lipinskis-rule-of-5) · [Upstream repository](https://github.com/rdkit/rdkit)
