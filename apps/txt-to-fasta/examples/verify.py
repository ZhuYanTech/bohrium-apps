import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'sequences.fasta'
assert file.is_file() and file.stat().st_size

assert file.read_text()==">seq_1\nMKTAYIA\n", file.read_text()
print("Sample output verified.")
