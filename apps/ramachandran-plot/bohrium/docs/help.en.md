## Inputs, settings and outputs

Upload PDB, ENT, or mmCIF, or enter a four-character PDB ID. The first model is analyzed. Residues require a complete, connected backbone. Download a PNG plot and per-residue CSV. Reference densities use a 2° grid, so classifications near contours can differ from interpolated methods. For 1UBQ expect at least 70 measured residues and angles within −180° to 180°.

`ramachandran.csv` reports chain, residue ID, reference class, angles, density, and classification. `ramachandran.png` plots the distributions and observations. Density at or above 0.02 is favored. Allowed cutoffs are 0.0005 for general, 0.002 for cis-proline, and 0.001 for the other four classes. Values below the class cutoff are outliers. The 1UBQ mmCIF example yields 74 measurable residues.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/ramachandran-plot) · [Upstream repository](https://github.com/rlabduke/rotarama_data)
