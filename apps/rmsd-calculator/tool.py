import copy
import csv
import json
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from Bio.PDB import MMCIFIO, PDBIO
from Bio.PDB.Polypeptide import is_aa
from helpers import option
from structure import get_structure, read_structure, structure_files

SELECTIONS={"ca","backbone","protein","heavy","all"}


def ranges(text):
    values=[]
    for item in text.split(","):
        if not item.strip():
            continue
        parts=list(map(int,item.split(":")))
        if len(parts)>2 or parts[0]>parts[-1]:
            raise ValueError("Invalid residue range.")
        values.append((parts[0],parts[-1]))
    return values


def selected(model, mode, limits, chain_id=None):
    results={}
    for chain in model:
        if chain_id is not None and chain.id!=chain_id:
            continue
        for res in chain:
            kind,num,icode=res.id
            if limits and not any(low<=num<=high for low,high in limits):
                continue
            if mode in {"ca","backbone","protein"} and (kind!=" " or not is_aa(res,standard=False)):
                continue
            for atom in res:
                if mode=="ca" and atom.name!="CA":
                    continue
                if mode=="backbone" and atom.name not in {"N","CA","C","O"}:
                    continue
                if mode=="heavy" and atom.element in {"H","D"}:
                    continue
                key=(chain.id if chain_id is None else "",kind,num,icode,atom.name)
                results[key]=atom
    return results


def matched(ref,mov,selection,limits,pair,mass):
    a=selected(ref,selection,limits,pair[0])
    b=selected(mov,selection,limits,pair[1])
    keys=sorted(a.keys() & b.keys())
    if not keys:
        raise ValueError("No corresponding selected atoms.")
    x=np.array([a[k].coord for k in keys],dtype=float)
    y=np.array([b[k].coord for k in keys],dtype=float)
    weights=np.array([a[k].mass if mass else 1 for k in keys],dtype=float)
    if not np.isfinite(weights).all() or (weights<=0).any():
        raise ValueError("A matched atom has no known mass.")
    return keys,x,y,weights,len(a),len(b)


def fit(x,y,w):
    if len(x)<3:
        raise ValueError("At least three matched fit atoms are required.")
    cx=np.average(x,axis=0,weights=w); cy=np.average(y,axis=0,weights=w)
    a=x-cx;b=y-cy
    if min(np.linalg.matrix_rank(a),np.linalg.matrix_rank(b))<2:
        raise ValueError("Fit atoms are collinear.")
    u,_,vt=np.linalg.svd((b*w[:,None]).T@a)
    if np.linalg.det(u@vt)<0:
        u[:,-1]*=-1
    rotation=u@vt
    return rotation,cx-cy@rotation


def chain_pairs(ref,mov,o):
    if o.compare_by=="structure":
        return [(None,None)]
    if o.compare_by=="chain":
        return [(a.id,b.id) for a in ref for b in mov]
    pairs=[]
    for value in o.chain_mapping.split(","):
        pair=value.strip().split(":")
        if len(pair)!=2 or not all(part.strip() for part in pair):
            raise ValueError("Use chain mappings such as A:X,B:Y.")
        pairs.append(tuple(" " if s.strip()=="(blank)" else s.strip() for s in pair))
    return pairs


def write(dest,name,header,rows):
    with (dest/name).open("w",encoding="utf-8",newline="") as handle:
        writer=csv.writer(handle); writer.writerow(header); writer.writerows(rows)


def run(o,dest):
    option(o.atoms,SELECTIONS);option(o.fit_atoms,SELECTIONS|{"same"})
    option(o.compare_by,{"structure","chain","mapped"});option(o.weighting,{"uniform","mass"});option(o.models,{"first","all"})
    fit_limits=ranges(o.fit_range); measure_limits=ranges(o.measure_range)
    use_mass=o.weighting=="mass"
    global_rows,residue_rows,transforms,warnings=[],[],[],[]
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        ref_path=get_structure(o.reference,o.reference_id,root)
        comparison_dir=root/"comparison";comparison_dir.mkdir()
        mov_path=get_structure(o.comparison,o.comparison_id,comparison_dir)
        refs=list(read_structure(ref_path).get_models())
        for path in structure_files(mov_path,root/"unpacked"):
            models=list(read_structure(path).get_models())
            for ref in refs[:1] if o.models=="first" else refs:
                for model in models[:1] if o.models=="first" else models:
                    for pair in chain_pairs(ref,model,o):
                        try:
                            keys,x,y,w,nref,nmov=matched(ref,model,o.atoms,measure_limits,pair,use_mass)
                            if o.align:
                                fit_keys,fx,fy,fw,_,_=matched(ref,model,o.atoms if o.fit_atoms=="same" else o.fit_atoms,fit_limits,pair,use_mass)
                                rotation,translation=fit(fx,fy,fw)
                                fit_count=len(fit_keys)
                            else:
                                fit_count=0
                                rotation,translation=np.eye(3),np.zeros(3)
                        except ValueError as error:
                            warnings.append(f"{path.stem} / {pair}: {error}")
                            continue
                        distances=np.linalg.norm(y@rotation+translation-x,axis=1)
                        original=np.linalg.norm(y-x,axis=1)
                        rmsd=float(np.sqrt(np.average(distances**2,weights=w)))
                        before=float(np.sqrt(np.average(original**2,weights=w)))
                        index=len(global_rows)+1
                        global_rows.append((index,ref_path.stem,path.stem,ref.id+1,model.id+1,pair[0],pair[1],len(keys),nref,nmov,rmsd,before,float(np.max(distances)),fit_count,len(keys)/nref,len(keys)/nmov,float(np.mean(distances))))
                        blocks=defaultdict(list)
                        for key,distance,weight in zip(keys,distances,w):
                            blocks[(key[0] or pair[0],key[2],key[3])].append((distance,weight))
                        for (chain,num,ins),pairs in blocks.items():
                            d,weight=np.array(pairs).T
                            residue_rows.append((index,chain,f"{num}{ins.strip()}",len(d),float(np.sqrt(np.average(d**2,weights=weight)))))
                        transforms.append({"comparison":index,"rotation":rotation.tolist(),"translation":translation.tolist(),"selection":o.atoms,"fit_selection":o.fit_atoms,"fit_range":o.fit_range,"measurement_range":o.measure_range,"weighting":o.weighting})
                        if o.fitted:
                            fitted=copy.deepcopy(model)
                            fitted.transform(rotation,translation)
                            use_cif=path.suffix.lower() in {".cif",".mmcif",".pdbx"}
                            io=MMCIFIO() if use_cif else PDBIO()
                            io.set_structure(fitted);io.save(str(dest/f"fitted_{index:03d}.{'cif' if use_cif else 'pdb'}"))
        if o.fitted:
            (dest/("reference"+ref_path.suffix.lower())).write_bytes(ref_path.read_bytes())
    (dest/"warnings.txt").write_text("\n".join(warnings),encoding="utf-8")
    if not global_rows:
        raise ValueError("No valid comparisons. " + " ".join(warnings[:3]))
    write(dest,"rmsd.csv",["comparison","reference","moving","reference_model","moving_model","reference_chain","moving_chain","matched_atoms","reference_atoms","moving_atoms","rmsd_A","unfitted_rmsd_A","max_displacement_A","fit_atoms","reference_coverage","moving_coverage","mean_displacement_A"],global_rows)
    write(dest,"per_residue.csv",["comparison","chain","residue","matched_atoms","rmsd_A"],residue_rows)
    (dest/"rmsd_transformations.json").write_text(json.dumps(transforms,indent=2),encoding="utf-8")
