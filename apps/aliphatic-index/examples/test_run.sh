#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT

python3 "$app_dir/run_aliphatic_index.py" "$app_dir/examples/example.fasta" --out-dir "$test_dir"
python3 - "$test_dir/aliphatic_index.csv" <<'PY'
import csv
import sys

with open(sys.argv[1], newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert [row["protein_id"] for row in rows] == ["alanine", "leucine", "mixed", "no-aliphatic"]
assert [float(row["aliphatic_index"]) for row in rows] == [100.0, 390.0, 292.5, 0.0]
assert all(row["length"] == "4" for row in rows)
assert all(rows[2][column] == "1" for column in ("ala_count", "val_count", "ile_count", "leu_count"))
PY

printf '>valid\nAVIL\n>invalid\nAX\n' > "$test_dir/invalid.fasta"
if python3 "$app_dir/run_aliphatic_index.py" "$test_dir/invalid.fasta" --out-dir "$test_dir/invalid"; then
    echo "Expected invalid input to fail" >&2
    exit 1
fi
test ! -e "$test_dir/invalid/aliphatic_index.csv"
