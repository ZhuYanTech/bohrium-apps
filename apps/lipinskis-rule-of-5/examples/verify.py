import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'lipinski.csv'
assert file.is_file() and file.stat().st_size
with file.open(encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
row,=rows; assert row["MW_Da"]=="180.16" and row["LogP"]=="1.31" and row["HBD"]=="1" and row["HBA"]=="3" and row["passes_Ro5"]=="True", row
print("Sample output verified.")
