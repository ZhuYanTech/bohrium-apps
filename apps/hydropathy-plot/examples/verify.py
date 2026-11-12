import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'hydropathy.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert len(rows)==6 and rows[0]["position"]=="3" and abs(float(rows[0]["hydropathy"])+.44)<1e-6; assert (dest/"hydropathy_001.png").stat().st_size>1000
print("Sample output verified.")
