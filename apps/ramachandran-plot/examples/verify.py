import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'ramachandran.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert len(rows)>=70 and all(-180<=float(r["phi"])<=180 and -180<=float(r["psi"])<=180 for r in rows); assert (dest/"ramachandran.png").read_bytes().startswith(b"\x89PNG")
print("Sample output verified.")
