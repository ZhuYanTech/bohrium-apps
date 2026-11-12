import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'converted.txt'
assert file.is_file() and file.stat().st_size

assert file.read_text()=="CYIQNCPLG\n", file.read_text()
print("Sample output verified.")
