## Inputs, settings and outputs

Upload FASTA/TXT/PDB, paste one protein sequence, or fetch FASTA by PDB ID. Upload a file for multiple sequences. Use an odd window from 5 to 21 (default 9). Each complete-window mean is assigned to its center. With MKTAYIAKQR and a window of 5, expect six scores starting at −0.44. Download the CSV and a PNG for each sequence.

`hydropathy.csv` reports sequence ID, center position, center residue, and score. Each sequence gets its own `hydropathy_*.png`. For the ten-residue example, positions 3–8 score −0.44, 0.08, 1.22, 0.58, −0.48, and −1.12.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/hydropathy-plot) · [Upstream repository](https://github.com/biopython/biopython)
