import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'summary.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
row,=rows; assert row["chains"]=="1" and row["residues"]=="76" and abs(float(row["total_sasa_A2"])-4888.35)<1.0, row
print("Sample output verified.")
