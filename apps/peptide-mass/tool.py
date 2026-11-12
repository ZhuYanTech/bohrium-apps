import csv
import math
from helpers import option
from proteins import read_proteins

AA = "ARNDCEQGHILKMFPSTWYV"
MONO = dict(zip(AA,[71.037114,156.101111,114.042927,115.026943,103.009185,129.042593,128.058578,57.021464,137.058912,113.084064,113.084064,128.094963,131.040485,147.068414,97.052764,87.032028,101.047679,186.079313,163.063329,99.068414]))
AVERAGE = dict(zip(AA,[71.0788,156.1875,114.1038,115.0886,103.1388,129.1155,128.1307,57.0519,137.1411,113.1594,113.1594,128.1741,131.1926,147.1766,97.1167,87.0782,101.1051,186.2132,163.1760,99.1326]))
CUT = {
    "trypsin": ("KR", False, True), "trypsin_all": ("KR", False, False),
    "lys_c": ("K", False, False), "arg_c": ("R", False, False), "asp_n": ("D", True, False),
    "glu_c_phosphate": ("DE", False, False), "glu_c_bicarbonate": ("E", False, False),
    "chymotrypsin": ("FYWML", False, True), "pepsin": ("FL", False, False),
    "proteinase_k": ("AEFILTVWY", False, False), "cnbr": ("M", False, False), "formic_acid": ("D", False, False),
}
MOD = {"none": (0,0), "cam": (57.021464,57.0513), "cm": (58.005479,58.0361), "vp": (105.057849,105.1372), "acrylamide": (71.037114,71.0788)}
CHARGE = {"h": 1, "neutral": 0, "minus_h": -1, "2h": 2, "3h": 3}
PROTON = 1.0072764666


def run(o, dest):
    option(o.enzyme,set(CUT))
    option(o.mass_type,{"mono","average"})
    option(o.cysteine,set(MOD))
    option(o.ion,set(CHARGE))
    option(o.sort_by,{"position","mass"})
    if not 0 <= o.missed <= 5:
        raise ValueError("Missed cleavages must be between 0 and 5.")
    low = float(o.min_mass) if o.min_mass else None
    high = float(o.max_mass) if o.max_mass else None
    if any(x is not None and (x<0 or not math.isfinite(x)) for x in (low,high)) or (low is not None and high is not None and low>high):
        raise ValueError("Invalid mass range.")
    residues,before,except_p = CUT[o.enzyme]
    mono = o.mass_type == "mono"
    weights = MONO if mono else AVERAGE
    water = 18.010565 if mono else 18.0153
    oxid = (15.994915 if mono else 15.9994) if o.oxidation else 0
    cysteine = MOD[o.cysteine][0 if mono else 1]
    charge = CHARGE[o.ion]
    rows=[]
    for name,sequence in read_proteins(o.sequence_file,o.sequence,o.pdb_id):
        sites = {0,len(sequence)}
        for i,aa in enumerate(sequence):
            if aa in residues and not (except_p and sequence[i+1:i+2]=="P"):
                sites.add(i if before else i+1)
        sites = sorted(sites)
        for i,start in enumerate(sites[:-1]):
            for missed,end in enumerate(sites[i+1:i+o.missed+2]):
                fragment = sequence[start:end]
                neutral = water + sum(weights[aa] for aa in fragment) + fragment.count("C")*cysteine + fragment.count("M")*oxid
                value = (neutral + charge*PROTON)/abs(charge) if charge else neutral
                if (low is not None and value < low) or (high is not None and value > high):
                    continue
                rows.append((name,start+1,end,fragment,len(fragment),value,missed))
    if o.sort_by=="mass":
        rows.sort(key=lambda row: row[5])
    with (dest/"peptides.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.writer(handle)
        writer.writerow(["protein_id","start","end","peptide","length","mass_or_mz","missed_cleavages"])
        writer.writerows((*row[:5],f"{row[5]:.4f}",row[6]) for row in rows)
