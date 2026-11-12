import csv
from io import StringIO
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski
from helpers import input_text


def read_compounds(text, suffix):
    if suffix in {".csv", ".tsv"}:
        rows = list(csv.reader(StringIO(text), delimiter="\t" if suffix == ".tsv" else ","))
        if not rows:
            return
        header = [c.strip().lower() for c in rows[0]]
        name_index = next((header.index(k) for k in ("name", "id", "compound") if k in header), None)
        if "smiles" in header:
            index = header.index("smiles")
            for row in rows[1:]:
                if row:
                    yield (row[index].strip() if len(row) > index else ""), (row[name_index].strip() if name_index is not None and len(row) > name_index else "")
        else:
            for row in rows:
                if not row:
                    continue
                if suffix == ".tsv" and len(row) > 1:
                    yield row[1].strip(), row[0].strip()
                else:
                    yield row[0].strip(), row[1].strip() if len(row) > 1 else ""
    else:
        for line in text.splitlines():
            parts = line.strip().split(maxsplit=1)
            if parts:
                yield parts[0], parts[1] if len(parts)>1 else ""


def run(o, dest):
    text = input_text(o.smiles_file, o.smiles)
    rows = list(read_compounds(text, o.smiles_file.suffix.lower() if o.smiles_file else ""))
    if not rows:
        raise ValueError("No compounds were supplied.")
    with (dest / "lipinski.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "smiles", "MW_Da", "LogP", "HBD", "HBA", "violations", "passes_Ro5", "status"])
        for i, (smiles, name) in enumerate(rows, 1):
            name = name or f"compound_{i}"
            mol = Chem.MolFromSmiles(smiles) if smiles else None
            if mol is None:
                writer.writerow([name, smiles, "", "", "", "", "", "", "Invalid SMILES"])
                continue
            mw, logp, donors, acceptors = Descriptors.MolWt(mol), Crippen.MolLogP(mol), Lipinski.NumHDonors(mol), Lipinski.NumHAcceptors(mol)
            violations = sum([mw > 500, logp > 5, donors > 5, acceptors > 10])
            writer.writerow([name, smiles, f"{mw:.2f}", f"{logp:.2f}", donors, acceptors, violations, violations <= 1, "OK"])
