import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'rmsd.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
row,=rows; assert row["matched_atoms"]=="76" and abs(float(row["rmsd_A"]))<1e-6, row; assert (dest/"rmsd_transformations.json").is_file()
print("Sample output verified.")
