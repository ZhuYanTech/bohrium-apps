## Inputs, settings and outputs

Upload PDB/ENT or enter a four-character PDB ID. Use observed or seqres, and all, protein, or nucleic. Enter comma-separated chain IDs or leave blank for all. Numbering gaps can be filled with X for proteins or N for nucleic acids. Recognized modified residues can be included. Header options are id_chain, title_chain, and chain. Width is 0, 60, 80, or 100. 1UBQ yields a 76-residue chain A.

`sequences.fasta` contains one record per chain. The defaults use coordinates, keep recognized modified residues, and wrap at 80 characters. `seqres` reads the structure’s SEQRES records. For a short title and 60-column wrapping on 1UBQ chain A, set the chain to A, the header to `chain`, and the width to 60.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/pdb-to-fasta) · [Upstream repository](https://github.com/biopython/biopython)
