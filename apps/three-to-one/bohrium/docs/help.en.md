## Inputs, settings and outputs

Upload TXT/FASTA/SEQ or paste one line of three-letter codes. Upload a file for multiple records. Delimiters include auto, space, hyphen, comma, tab, semicolon, and custom. Unknown options are x, skip, error, and bracket. Set output case, FASTA header preservation, and wrap width. Cys-Tyr-Ile-Gln-Asn-Cys-Pro-Leu-Gly gives CYIQNCPLG. Extract Word or PDF text first.

The defaults recognize whitespace, commas, and hyphens, convert unknown codes to X, preserve FASTA headers, and produce uppercase letters. With `custom`, delimiter `/`, and `bracket`, `Ala/unknown/Arg` yields `A[unknown]R`. Download `converted.txt` and check `run.log` for the unknown-code count.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/three-to-one)
