#!/usr/bin/env python3
"""Calculate the Ikai aliphatic index from standard protein FASTA records."""

import argparse
from collections import Counter
import csv
from io import StringIO
from pathlib import Path
import re
from urllib.request import urlopen


STANDARD_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWY")
FIELDS = ("protein_id", "length", "ala_count", "val_count", "ile_count",
          "leu_count", "aliphatic_index")


def read_fasta(fasta: str) -> list[tuple[str, list[str]]]:
    if fasta.strip() and not fasta.lstrip().startswith(">"):
        return [("Sequence", fasta.splitlines())]
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

    return records


def read_csv(content: str) -> list[tuple[str, list[str]]]:
    reader = csv.DictReader(StringIO(content), strict=True)
    fields = {name.strip().lower(): name for name in reader.fieldnames or []}
    id_field = fields.get("id") or fields.get("name")
    sequence_field = fields.get("sequence") or fields.get("seq")
    if not id_field or not sequence_field:
        raise ValueError("CSV 需要 id/name 和 sequence/seq 两列。")
    records = []
    for row in reader:
        name, sequence = row.get(id_field), row.get(sequence_field)
        if None in row or not name or not name.strip() or sequence is None:
            raise ValueError(f"CSV 第 {reader.line_num} 行缺少编号或序列，或列数不匹配。")
        records.append((re.split(r"[\s|]", name.strip(), maxsplit=1)[0], [sequence]))
    return records


def read_pdb(content: str, identifier: str) -> list[tuple[str, list[str]]]:
    from Bio.Data.PDBData import protein_letters_3to1, protein_letters_3to1_extended

    chains: dict[str, list[str]] = {}
    seen = set()
    for line in content.splitlines():
        if line.startswith("ENDMDL"):
            break
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        residue = line[17:20]
        if residue in {"A  ", "C  ", "G  ", "U  ", "I  ", " DA", " DC", " DG", " DT", " DI"}:
            continue
        letter = protein_letters_3to1_extended.get(residue)
        if line.startswith("HETATM") and letter is None:
            continue
        chain = line[21:22].strip() or "_"
        key = (chain, line[22:27])
        if key in seen:
            continue
        seen.add(key)
        if letter is None:
            letter = protein_letters_3to1.get(residue.strip())
        if letter is None:
            raise ValueError(f"PDB 链 {chain} 含未知残基 {residue.strip()}。")
        chains.setdefault(chain, []).append(letter)
    return [(f"{identifier}_{chain}", sequence) for chain, sequence in chains.items()]


def fetch_fasta(pdb_id: str) -> str:
    if not re.fullmatch(r"[0-9][A-Za-z0-9]{3}", pdb_id):
        raise ValueError("PDB 编号应为 4 位，以数字开头。")
    with urlopen(f"https://www.rcsb.org/fasta/entry/{pdb_id.upper()}/display", timeout=20) as response:
        return response.read().decode("utf-8")


def calculate(fasta: str, input_format: str = "fasta", identifier: str = "structure") -> list[dict]:
    if input_format == "csv":
        records = read_csv(fasta)
    elif input_format == "pdb":
        records = read_pdb(fasta, identifier)
    else:
        records = read_fasta(fasta)
    if not records:
        raise ValueError("没有可计算的蛋白质序列。")
    results = []
    for protein_id, lines in records:
        raw_sequence = "".join("".join(lines).split())
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


def write_results(fasta: str, output: Path, input_format: str = "fasta", identifier: str = "structure") -> int:
    rows = calculate(fasta, input_format, identifier)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "aliphatic_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (output / "results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("Protein ID", "Amino acids", "Aliphatic index"))
        for row in rows:
            writer.writerow((row["protein_id"], row["length"], f'{float(row["aliphatic_index"]):.2f}'))
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fasta", type=Path, help="输入 FASTA 文件")
    parser.add_argument("--out-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        count = write_results(args.fasta.read_text(encoding="utf-8-sig"), args.out_dir,
                              args.fasta.suffix.lower()[1:], args.fasta.stem)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(f"完成 {count} 条序列的脂肪族指数计算。")


if __name__ == "__main__":
    main()
