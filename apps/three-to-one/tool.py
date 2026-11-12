import re
from helpers import fasta_records, input_text, option, wrapped

CODES = dict(zip(
    "ALA ARG ASN ASP CYS GLU GLN GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL ASX GLX XLE SEC PYL UNK".split(),
    "ARNDCEQGHILKMFPSTWYVBZJUOX",
))
DELIMITERS = {"hyphen": "-", "space": " ", "comma": ",", "tab": "\t", "semicolon": ";"}


def tokens(line, delimiter, custom):
    if delimiter == "auto":
        parts = re.split(r"[-,\s]+", line.strip())
    elif delimiter == "space":
        return line.split()
    else:
        separator = custom if delimiter == "custom" else DELIMITERS[delimiter]
        if separator:
            return [part.strip() for part in line.split(separator) if part.strip()]
        parts = [line.strip()]
    return [part[i:i+3] for part in parts if part for i in range(0, len(part), 3)]


def run(o, dest):
    option(o.delimiter, set(DELIMITERS) | {"auto", "custom"})
    option(o.unknown, {"x", "skip", "error", "bracket"})
    option(o.letter_case, {"upper", "lower"})
    text = input_text(o.text_file, o.sequence)
    records = fasta_records(text)
    unknown_count = 0
    output = []
    for name, content in records:
        translated = []
        for line in content.splitlines():
            for token in tokens(line, o.delimiter, o.custom_delimiter):
                code = token.upper()
                if code in CODES:
                    translated.append(CODES[code])
                    continue
                unknown_count += 1
                if o.unknown == "error":
                    raise ValueError(f"Unknown three-letter residue: {token}")
                if o.unknown == "x":
                    translated.append("X")
                elif o.unknown == "bracket":
                    translated.append(f"[{token}]")
        sequence = "".join(translated)
        if o.letter_case == "lower":
            sequence = sequence.lower()
        if o.preserve_fasta and text.lstrip().startswith(">"):
            output.append(">" + name)
        output.append(wrapped(sequence, o.wrap))
    if not records or not any(line and not line.startswith(">") for line in output):
        raise ValueError("No converted sequence residues remain.")
    (dest / "converted.txt").write_text("\n".join(output) + "\n", encoding="utf-8")
    (dest / "run.log").write_text(f"Records: {len(records)}\nUnknown tokens: {unknown_count}\n", encoding="utf-8")
