#!/usr/bin/env python3
"""Calculate the Ikai aliphatic index from standard protein FASTA records."""

import argparse
from collections import Counter
import csv
from pathlib import Path
import re


STANDARD_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWY")
FIELDS = ("protein_id", "length", "ala_count", "val_count", "ile_count",
          "leu_count", "aliphatic_index")


def calculate(fasta: str) -> list[dict]:
    records: list[tuple[str, list[str]]] = []
    for number, raw_line in enumerate(fasta.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            header = line[1:].strip()
            protein_id = re.split(r"[\s|]", header, maxsplit=1)[0]
            if not protein_id:
                raise ValueError(f"第 {number} 行缺少 FASTA 记录编号。")
            records.append((protein_id, []))
        else:
            if not records:
                raise ValueError(f"第 {number} 行缺少 FASTA 标题（以 > 开头）。")
            records[-1][1].append(line)

    if not records:
        raise ValueError("请输入至少一条 FASTA 记录。")

    results = []
    for protein_id, lines in records:
        raw_sequence = "".join(lines)
        if not raw_sequence:
            raise ValueError(f"记录 {protein_id} 缺少序列。")
        invalid = set(raw_sequence) - STANDARD_RESIDUES - {r.lower() for r in STANDARD_RESIDUES}
        if invalid:
            invalid_text = ", ".join(repr(residue) for residue in sorted(invalid))
            raise ValueError(f"记录 {protein_id} 含无效残基 {invalid_text}。仅接受 20 种标准氨基酸。")
        counts = Counter(raw_sequence.upper())
        length = len(raw_sequence)
        weighted_tenths = 10 * counts["A"] + 29 * counts["V"] + 39 * (counts["I"] + counts["L"])
        results.append(dict(zip(FIELDS, (
            protein_id, length, counts["A"], counts["V"], counts["I"],
            counts["L"], f"{10 * weighted_tenths / length:.6f}",
        ))))
    return sorted(results, key=lambda row: row["protein_id"])


def write_results(fasta: str, output: Path) -> int:
    rows = calculate(fasta)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "aliphatic_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fasta", type=Path, help="输入 FASTA 文件")
    parser.add_argument("--out-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        count = write_results(args.fasta.read_text(encoding="utf-8-sig"), args.out_dir)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(f"完成 {count} 条序列的脂肪族指数计算。")


if __name__ == "__main__":
    main()
