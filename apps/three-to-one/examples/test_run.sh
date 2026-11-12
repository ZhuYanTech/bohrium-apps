#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT
python3 launching.py --sequence Cys-Tyr-Ile-Gln-Asn-Cys-Pro-Leu-Gly --output_dir "$test_dir/valid"
python3 examples/verify.py "$test_dir/valid"
if python3 launching.py --output_dir "$test_dir/invalid"; then
    echo "Empty input was expected to fail" >&2
    exit 1
fi
