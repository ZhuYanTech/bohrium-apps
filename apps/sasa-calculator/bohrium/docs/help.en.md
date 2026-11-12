## Inputs, settings and outputs

Upload PDB, ENT, mmCIF, or a ZIP of structures, or enter a PDB ID. Use a probe radius of 1.4, 1.8, or 2.0 Å. Each heavy atom is sampled at 92 points. Download residue, chain, and structure CSVs. Relative accessibility is reported at 1.4 Å and omitted for termini and residues without a reference. For 1UBQ expect one chain, 76 residues, and about 4,888 Å².

`residues.csv` gives residue areas and exposure labels, while `chains.csv` and `summary.csv` give totals. RSA below 20% is buried and above 50% is exposed. Values between those cutoffs are intermediate. Termini and residues without a reference area have an explanation in place of an RSA value. For 1UBQ the 1.4 Å and 1.8 Å totals are 4,888.35 and 4,837.27 Å².

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/sasa-calculator) · [Upstream repository](https://github.com/biopython/biopython)
