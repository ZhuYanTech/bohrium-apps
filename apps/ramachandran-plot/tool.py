import csv
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
from Bio.PDB.vectors import calc_dihedral
from Bio.Data.PDBData import protein_letters_3to1_extended
from structure import get_structure, read_structure

TABLES = {
    "general": ("general-noGPIVpreP", .0005), "glycine": ("gly-sym", .001),
    "cis-proline": ("cispro", .002), "trans-proline": ("transpro", .001),
    "pre-proline": ("prepro-noGP", .001), "ile-val": ("ileval-nopreP", .001),
}


def cell(angle):
    return int(((angle+180)%360)//2)


def tables():
    grids={}
    for kind,(name,_) in TABLES.items():
        grid=np.zeros((180,180))
        path=Path(__file__).parent/"data"/f"rama8000-{name}.data"
        for line in path.read_text().splitlines():
            if line and not line.startswith("#"):
                x,y,z=map(float,line.split())
                grid[cell(y),cell(x)]=z
        grids[kind]=grid
    return grids


def angles(a,b,c):
    cn,c0,n0,ca0,n1=[atom.get_vector() for atom in (a["CA"],a["C"],b["N"],b["CA"],c["N"])]
    if (c0-n0).norm()>1.8 or (b["C"].get_vector()-n1).norm()>1.8:
        return None
    phi=math.degrees(calc_dihedral(c0,n0,ca0,b["C"].get_vector()))
    psi=math.degrees(calc_dihedral(n0,ca0,b["C"].get_vector(),n1))
    omega=math.degrees(calc_dihedral(cn,c0,n0,ca0))
    return phi,psi,omega


def run(o,dest):
    grids=tables()
    rows=[]
    with TemporaryDirectory() as tmp:
        path=get_structure(o.structure,o.pdb_id,Path(tmp))
        model=next(read_structure(path).get_models())
        for chain in model:
            polymer=[r for r in chain if r.resname in protein_letters_3to1_extended]
            for prev,res,next_res in zip(polymer,polymer[1:],polymer[2:]):
                try:
                    values=angles(prev,res,next_res)
                except KeyError:
                    continue
                if values is None:
                    continue
                phi,psi,omega=values
                aa=res.resname
                if aa=="GLY": kind="glycine"
                elif aa=="PRO": kind="cis-proline" if -90<omega<90 else "trans-proline"
                elif next_res.resname=="PRO": kind="pre-proline"
                elif aa in {"ILE","VAL"}: kind="ile-val"
                else: kind="general"
                density=grids[kind][cell(psi),cell(phi)]
                status="favored" if density>=.02 else ("allowed" if density>=TABLES[kind][1] else "outlier")
                rows.append((chain.id,f"{res.id[1]}{res.id[2].strip()}",aa,kind,phi,psi,density,status))
    if not rows:
        raise ValueError("No residues with complete, connected backbone triplets were found.")
    with (dest/"ramachandran.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.writer(handle);writer.writerow(["chain","position","residue","class","phi","psi","density","classification"]);writer.writerows(rows)
    fig,axes=plt.subplots(2,3,figsize=(10.8,7),layout="constrained",sharex=True,sharey=True)
    for (kind,(_,threshold)),ax in zip(TABLES.items(),axes.flat):
        ax.contourf(np.arange(-179,180,2),np.arange(-179,180,2),grids[kind],levels=[threshold,.02,1.01],colors=["#dbe9f4","#92bccf"])
        group=[r for r in rows if r[3]==kind]
        ax.scatter([r[4] for r in group],[r[5] for r in group],c=["#b34031" if r[-1]=="outlier" else "#183943" for r in group],s=11)
        ax.set(xlim=(-180,180),ylim=(-180,180),title=kind,xlabel="φ (°)",ylabel="ψ (°)",aspect="equal")
    fig.savefig(dest/"ramachandran.png",dpi=170)
    plt.close(fig)
