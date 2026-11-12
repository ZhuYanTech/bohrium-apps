import re
from urllib.request import urlopen
from helpers import fasta_records

STANDARD = set("ACDEFGHIKLMNPQRSTVWY")


def read_proteins(file, sequence, pdb_id):
    if sum(map(bool, (file, sequence.strip(), pdb_id.strip()))) != 1:
        raise ValueError("Provide exactly one sequence file, sequence text, or PDB ID.")
    if pdb_id:
        if not re.fullmatch(r"[0-9][A-Za-z0-9]{3}", pdb_id.strip()):
            raise ValueError("Expected a four-character PDB ID.")
        with urlopen(f"https://www.rcsb.org/fasta/entry/{pdb_id.strip().upper()}/display", timeout=25) as response:
            text = response.read().decode("utf-8")
    elif file and file.suffix.lower() in {".pdb", ".ent"}:
        from Bio.Data.PDBData import protein_letters_3to1_extended
        from structure import read_structure

        model = next(read_structure(file).get_models())
        rows = [(f"{file.stem}_{chain.id}", "".join(protein_letters_3to1_extended.get(res.resname, "X")
                 for res in chain if res.id[0] == " " or res.resname in protein_letters_3to1_extended)) for chain in model]
        return validate([(name, seq) for name, seq in rows if seq])
    else:
        text = file.read_text(encoding="utf-8-sig") if file else sequence
    return validate(fasta_records(text))


def validate(rows):
    if not rows:
        raise ValueError("No protein sequences were found.")
    result = []
    for name, raw in rows:
        seq = "".join(raw.split()).upper()
        if not seq or set(seq) - STANDARD:
            raise ValueError(f"Record {name}: expected a nonempty sequence of standard amino acids.")
        result.append((name, seq))
    return result
