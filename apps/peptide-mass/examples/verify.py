import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'peptides.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert [(r["peptide"],r["mass_or_mz"]) for r in rows]==[("AK","218.1499"),("R","175.1190")], rows
print("Sample output verified.")
