## Choose one input method

- **Paste sequence**: One plain protein sequence or multiple FASTA records. Plain input is labeled `Sequence`.
- **Upload a file**: FASTA (`.fasta/.fa/.fas/.faa`), TXT, CSV, or PDB. CSV accepts `id,sequence` or `name,seq`. PDB parsing uses coordinate-bearing protein chains in the first model and maps recognized modified residues such as MSE.
- **Structure ID**: Enter a four-character RCSB PDB ID to retrieve FASTA. Lookup requires network access to RCSB.

Use the 20 standard amino acid letters. Case and whitespace are ignored. An empty record or an invalid residue stops the batch. Select a CPU machine and submit. The calculation has fixed coefficients.

## Example and output

Paste `AV IL` to get ID `Sequence`, length 4, and an index of **292.50**. The introduction provides the insulin example.

`results.csv` contains ID, length, and the aliphatic index to two decimal places. `aliphatic_index.csv` adds A/V/I/L counts and reports the index to six decimal places. Both files are sorted by ID.

[Open-source implementation and usage guide](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/aliphatic-index)
