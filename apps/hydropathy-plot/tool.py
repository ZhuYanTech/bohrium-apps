import csv
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from proteins import read_proteins

KD = dict(zip("ACDEFGHIKLMNPQRSTVWY",[1.8,2.5,-3.5,-3.5,2.8,-0.4,-3.2,4.5,-3.9,3.8,1.9,-3.5,-1.6,-3.5,-4.5,-0.8,-0.7,4.2,-0.9,-1.3]))


def run(o, dest):
    if not (5 <= o.window <= 21 and o.window % 2):
        raise ValueError("Use an odd window from 5 through 21.")
    sequences = read_proteins(o.sequence_file,o.sequence,o.pdb_id)
    values=[]
    for index,(name,seq) in enumerate(sequences,1):
        scores = [sum(KD[a] for a in seq[i:i+o.window])/o.window for i in range(len(seq)-o.window+1)]
        if not scores:
            print(f"{name}: no complete window.")
            continue
        positions = range(o.window//2+1,len(scores)+o.window//2+1)
        values.extend((name,pos,seq[pos-1],f"{score:.4f}") for pos,score in zip(positions,scores))
        fig, ax = plt.subplots(figsize=(8,3.4),layout="constrained")
        ax.plot(positions,scores,color="#006a71",linewidth=1.6)
        ax.axhline(0,color="#6a7176",linewidth=.7)
        ax.set(xlabel="Residue position",ylabel="Mean Kyte–Doolittle score",title=f"{name[:60]} · window {o.window}")
        fig.savefig(dest/f"hydropathy_{index:03d}.png",dpi=170)
        plt.close(fig)
    if not values:
        raise ValueError("All sequences are shorter than the selected window.")
    with (dest/"hydropathy.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.writer(handle); writer.writerow(["protein_id","position","residue","hydropathy"]);writer.writerows(values)
