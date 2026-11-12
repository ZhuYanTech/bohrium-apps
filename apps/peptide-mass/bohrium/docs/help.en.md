## Inputs, settings and outputs

Upload FASTA/TXT, paste a protein sequence, or fetch FASTA by PDB ID. Set cleavage rule, 0–5 missed cleavages, mono/average mass, ion type, cysteine modification, methionine oxidation, mass range, and sorting. Trypsin and [M+H]⁺ are defaults. For AKR expect AK at 218.1499 and R at 175.1190. Cleavage rules are sequence-based approximations.

Cleavage codes are `trypsin`, `trypsin_all`, `lys_c`, `arg_c`, `asp_n`, `glu_c_phosphate`, `glu_c_bicarbonate`, `chymotrypsin`, `pepsin`, `proteinase_k`, `cnbr`, and `formic_acid`. Ion codes are `h`, `neutral`, `minus_h`, `2h`, and `3h`. Cysteine options are `none`, `cam`, `cm`, `vp`, and `acrylamide`. Positions in `peptides.csv` are 1-based and values are reported to four decimal places.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/peptide-mass)
