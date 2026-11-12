## Inputs, settings and outputs

Upload plain text, FASTA, CSV/TSV, or paste a single line. Tables use a sequence or seq column and optionally name or id. Upload multi-line or multi-record input. Group by auto, blank, join, or custom. Set naming, letter case, wrap width, and validation (lenient, strict, or off). Gaps and stops can be kept. Input 1 mkt ayia yields MKTAYIA. run.log records skipped records. Extract Word or PDF text before uploading.

The defaults use automatic grouping and type, preserve recognized names, and output unwrapped uppercase text. Select `join` to merge a headerless sequence. Custom grouping requires a delimiter. Tables must contain a `sequence` or `seq` column. Download `sequences.fasta` and `run.log` to check the record count and skipped inputs.

[Open-source implementation](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/txt-to-fasta)
