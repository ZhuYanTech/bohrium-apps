import csv
from pathlib import Path
import sys

dest = Path(sys.argv[1])
file = dest / 'sequences.fasta'
assert file.is_file() and file.stat().st_size

text=file.read_text(); assert text.startswith(">1UBQ_A\n") and len("".join(text.splitlines()[1:]))==76, text
print("Sample output verified.")
