import math
import re
import shlex
import subprocess
from helpers import option

FORMATS = {"smi","can","mol","sdf","mol2","pdb","pdbqt","xyz","cif","inchi","cml","cdx","fasta","molreport"}
HYDROGENS = {"none": [], "add": ["-h"], "polar": ["--addpolarh"], "nonpolar": ["--addnonpolarh"], "delete": ["-d"], "delete_nonpolar": ["--delnonpolarh"]}
COORDINATES = {"none": [], "2d": ["--gen2d"], "3d": ["--gen3d"]}
FORCE_FIELDS = {"none", "MMFF94", "MMFF94s", "UFF", "GAFF", "Ghemical"}


def guess(text, suffix):
    if suffix in {"smiles", "smi"}:
        return "smi"
    if suffix in FORMATS:
        return suffix
    stripped = text.lstrip()
    if stripped.startswith("InChI="):
        return "inchi"
    if stripped.startswith(("data_", "loop_")):
        return "cif"
    if "@<TRIPOS>MOLECULE" in text:
        return "mol2"
    if "M  END" in text:
        return "sdf" if "$$$$" in text else "mol"
    if re.search(r"^(ROOT|BRANCH|TORSDOF)", text, re.M):
        return "pdbqt"
    if re.search(r"^(ATOM  |HETATM|HEADER)", text, re.M):
        return "pdb"
    if stripped.splitlines() and stripped.splitlines()[0].isdigit():
        return "xyz"
    return "fasta" if stripped.startswith(">") else "smi"


def run(o, dest):
    if bool(o.molecule_file) == bool(o.molecule_text.strip()):
        raise ValueError("Provide exactly one molecule file or text.")
    if o.molecule_file and o.molecule_file.stat().st_size > 10 * 1024**2:
        raise ValueError("Input exceeds 10 MiB.")
    raw = o.molecule_file.read_bytes() if o.molecule_file else o.molecule_text.encode()
    text = raw.decode("utf-8", "replace")
    in_format = guess(text, o.molecule_file.suffix.lower()[1:] if o.molecule_file else "") if o.input_format == "auto" else o.input_format
    option(in_format, FORMATS)
    option(o.output_format, FORMATS)
    option(o.coordinates, set(COORDINATES))
    option(o.hydrogens, set(HYDROGENS))
    option(o.charges, {"none", "gasteiger"})
    option(o.force_field, FORCE_FIELDS)
    if o.ph and not math.isfinite(float(o.ph)):
        raise ValueError("pH must be finite.")
    if o.force_field != "none" and o.coordinates != "3d" and in_format in {"smi","can","inchi","fasta"}:
        raise ValueError("Generate 3D coordinates before minimizing text without coordinates.")
    cmd = ["obabel", "-i"+in_format, "-o"+o.output_format]
    cmd += COORDINATES[o.coordinates] + HYDROGENS[o.hydrogens]
    if o.ph:
        cmd += ["-p", str(float(o.ph))]
    if o.charges != "none":
        cmd += ["--partialcharge", "gasteiger"]
    if o.force_field != "none":
        cmd += ["--minimize", "--ff", o.force_field, "--steps", str(o.minimization_steps)]
    try:
        result = subprocess.run(cmd, input=raw, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Open Babel conversion exceeded 120 seconds.") from exc
    log = result.stderr.decode("utf-8", "replace")
    (dest / "run.log").write_text(shlex.join(cmd) + "\n" + log, encoding="utf-8")
    if result.returncode or not result.stdout or re.search(r"\b0 molecules converted", log):
        raise ValueError("Open Babel returned no output. See run.log.")
    (dest / ("converted."+o.output_format)).write_bytes(result.stdout)
