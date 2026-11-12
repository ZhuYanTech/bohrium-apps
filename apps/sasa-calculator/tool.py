import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from Bio.Data.PDBData import protein_letters_3to1_extended
from Bio.Data.PDBData import residue_sasa_scales
from Bio.PDB.SASA import ShrakeRupley
from structure import get_structure, read_structure, structure_files

MAX_AREA = residue_sasa_scales["Wilke"]
NUCLEIC = {"A","C","G","U","I","DA","DC","DG","DT","DI"}


def write(dest, name, fields, rows):
    with (dest/name).open("w",encoding="utf-8",newline="") as handle:
        writer=csv.writer(handle);writer.writerow(fields);writer.writerows(rows)


def run(o,dest):
    if o.probe_radius not in {1.4,1.8,2.0}:
        raise ValueError("Probe radius must be 1.4, 1.8, or 2.0 Å.")
    residues,chains,structures=[],[],[]
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        input_path=get_structure(o.structure,o.pdb_id,root)
        for path in structure_files(input_path,root/"unpacked"):
            model=next(read_structure(path).get_models())
            for chain in list(model):
                for residue in list(chain):
                    if residue.resname not in NUCLEIC and residue.resname not in protein_letters_3to1_extended and residue.id[0] != " ":
                        chain.detach_child(residue.id)
                        continue
                    for atom in list(residue):
                        if atom.element in {"H","D"}:
                            residue.detach_child(atom.id)
                    if not len(residue):
                        chain.detach_child(residue.id)
                if not len(chain):
                    model.detach_child(chain.id)
            if not len(model):
                raise ValueError(f"No polymer atoms in {path.name}.")
            ShrakeRupley(probe_radius=o.probe_radius,n_points=92).compute(model,level="R")
            total,count=0,0
            for chain in model:
                chain_rows=list(chain)
                chain_total=sum(res.sasa for res in chain_rows)
                total+=chain_total; count+=len(chain_rows)
                chains.append((path.stem,chain.id,len(chain_rows),f"{chain_total:.2f}"))
                for i,res in enumerate(chain_rows):
                    max_sasa=MAX_AREA.get(res.resname)
                    rsa,exposure,note="","",""
                    if o.probe_radius!=1.4:
                        note="Needs 1.4 Å probe"
                    elif i in {0,len(chain_rows)-1}:
                        note="Chain terminus"
                    elif not max_sasa:
                        note="No protein reference area"
                    else:
                        raw=res.sasa/max_sasa*100
                        rsa=f"{raw:.1f}"
                        exposure="Buried" if raw<20 else ("Exposed" if raw>50 else "Intermediate")
                    residues.append((path.stem,chain.id,res.resname,f"{res.id[1]}{res.id[2].strip()}",f"{res.sasa:.2f}",rsa,exposure,note))
            structures.append((path.stem,f"{total:.2f}",len(model),count))
    write(dest,"residues.csv",["structure","chain","residue","position","sasa_A2","rsa_pct","exposure","rsa_note"],residues)
    write(dest,"chains.csv",["structure","chain","residues","sasa_A2"],chains)
    write(dest,"summary.csv",["structure","total_sasa_A2","chains","residues"],structures)
