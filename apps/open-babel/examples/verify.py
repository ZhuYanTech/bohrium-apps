import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'converted.mol'
assert file.is_file() and file.stat().st_size

assert "M  END" in file.read_text() and file.read_text().splitlines()[3][:3].strip()=="3"
print("Sample output verified.")
