from collections import defaultdict
from tempfile import TemporaryDirectory
from pathlib import Path
from Bio.Data.PDBData import protein_letters_3to1, protein_letters_3to1_extended
from helpers import option, wrapped
from structure import get_structure

NA = dict(zip(("A","C","G","U","I","DA","DC","DG","DT","DI"),"ACGUIACGTI"))


def residue(code, modified):
    if code in NA:
        return NA[code], "nucleic"
    if code in protein_letters_3to1:
        return protein_letters_3to1[code], "protein"
    if modified and code in protein_letters_3to1_extended:
        return protein_letters_3to1_extended[code], "protein"
    return None, None


def run(o, dest):
    option(o.sequence_source,{"observed","seqres"})
    option(o.molecule_type,{"all","protein","nucleic"})
    option(o.header_format,{"id_chain","title_chain","chain"})
    if o.wrap not in {0,60,80,100}:
        raise ValueError("Line wrapping accepts 0, 60, 80 or 100.")
    with TemporaryDirectory() as tmp:
        file = get_structure(o.structure,o.pdb_id,Path(tmp),"pdb")
        lines = file.read_text(encoding="ascii",errors="replace").splitlines()
        stem = file.stem
    if not lines:
        raise ValueError("Empty PDB file.")
    title = " ".join(line[10:].strip() for line in lines if line.startswith("TITLE "))
    pdb_id = next((line[62:66].strip() for line in lines if line.startswith("HEADER") and line[62:66].strip()), stem)
    rows=defaultdict(list)
    seen=set()
    if o.sequence_source=="seqres":
        for line in lines:
            if line.startswith("SEQRES"):
                chain = line[11:12].strip() or "_"
                rows[chain].extend((code,None) for code in line[19:70].split())
    else:
        for line in lines:
            if line.startswith("ENDMDL"):
                break
            if line.startswith(("ATOM  ","HETATM")):
                code=line[17:20].strip()
                if line.startswith("HETATM") and residue(code,True)[0] is None:
                    continue
                chain=line[21:22].strip() or "_"
                key=chain,line[22:27]
                if key in seen:
                    continue
                seen.add(key)
                try:
                    number=int(line[22:26])
                except ValueError:
                    number=None
                rows[chain].append((code,number))
    wanted={s.strip() for s in o.chains.split(",") if s.strip()}
    records=[]
    for chain,entries in rows.items():
        if wanted and chain not in wanted:
            continue
        mapped = [(residue(code,o.include_modified),number) for code,number in entries]
        kinds = {kind for (char,kind),_ in mapped if char}
        if o.molecule_type!="all" and o.molecule_type not in kinds:
            continue
        letters=[]
        previous=None
        for (char,kind),number in mapped:
            if not char or (o.molecule_type!="all" and kind!=o.molecule_type):
                continue
            if o.insert_gaps and previous is not None and number is not None and number>previous+1:
                gap=number-previous-1
                if gap>10000:
                    raise ValueError("Residue numbering gap exceeds 10,000.")
                letters.append(("N" if kind=="nucleic" else "X")*gap)
            letters.append(char)
            previous=number
        if letters:
            header={"chain":chain,"id_chain":f"{pdb_id}_{chain}","title_chain":f"{title or pdb_id}_{chain}"}[o.header_format]
            records.append(">"+header+"\n"+wrapped("".join(letters),o.wrap))
    if not records:
        raise ValueError("No sequences matched the requested source and chain settings.")
    (dest/"sequences.fasta").write_text("\n".join(records)+"\n",encoding="utf-8")
