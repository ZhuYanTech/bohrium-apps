import csv
from io import StringIO
import re
from helpers import fasta_records, input_text, option, wrapped

ALPHABETS = {
    "dna": set("ACGTRYSWKMBDHVN"),
    "rna": set("ACGURYSWKMBDHVN"),
    "nucleotide": set("ACGTURYSWKMBDHVN"),
    "protein": set("ACDEFGHIKLMNPQRSTVWYBXZJUO"),
}


def parse(text, mode, separator, file):
    if text.lstrip().startswith(">"):
        return fasta_records(text)
    if file and file.suffix.lower() in {".csv", ".tsv"}:
        reader = csv.DictReader(StringIO(text), delimiter="\t" if file.suffix.lower() == ".tsv" else ",")
        keys = {k.lower().strip(): k for k in (reader.fieldnames or [])}
        seq = keys.get("sequence") or keys.get("seq")
        name = keys.get("id") or keys.get("name")
        if not seq:
            raise ValueError("Table requires sequence or seq column.")
        return [(row.get(name) or "", row.get(seq) or "") for row in reader]
    if mode == "custom":
        if not separator:
            raise ValueError("Custom mode requires a separator.")
        blocks = text.split(separator)
    elif mode in {"blank", "auto"}:
        blocks = re.split(r"\n\s*\n", text.strip())
    else:
        blocks = [text]
    rows = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if mode == "auto" and all("\t" in line for line in lines):
            rows.extend(tuple(line.split("\t", 1)) for line in lines)
        elif len(lines) > 1 and (":" in lines[0] or re.search(r"[a-z] [A-Za-z]", lines[0])) and not re.match(r"\d", lines[0]):
            rows.append((lines[0].rstrip(":"), "\n".join(lines[1:])))
        else:
            rows.append(("", "\n".join(lines)))
    return rows


def run(o, dest):
    option(o.multi, {"auto", "blank", "join", "custom"})
    option(o.sequence_type, set(ALPHABETS) | {"auto"})
    option(o.names, {"input", "numbered"})
    option(o.letter_case, {"upper", "lower", "original"})
    option(o.validation, {"lenient", "strict", "off"})
    rows = parse(input_text(o.text_file, o.sequence), o.multi, o.separator, o.text_file)
    alphabet = ALPHABETS.get(o.sequence_type, ALPHABETS["protein"] | ALPHABETS["nucleotide"])
    extras = ("-" if o.keep_gaps else "") + ("*" if o.keep_stops else "")
    output, notices = [], []
    for number, (name, content) in enumerate(rows, 1):
        if (o.sequence_type == "dna" and "U" in content.upper()) or (o.sequence_type == "rna" and "T" in content.upper()):
            notices.append(f"Record {number}: T/U conflicts with the selected type.")
            continue
        cleaned = "".join(c for c in content if c in extras or c.upper() in alphabet or (o.validation == "off" and c.isascii() and c.isalpha()))
        if o.validation == "strict" and cleaned != content.replace("\n", ""):
            notices.append(f"Record {number}: strict validation failed.")
            continue
        if not cleaned:
            notices.append(f"Record {number}: no sequence characters.")
            continue
        if o.letter_case != "original":
            cleaned = cleaned.upper() if o.letter_case == "upper" else cleaned.lower()
        header = name.strip() if o.names == "input" and name.strip() else f"seq_{number}"
        output.append(">" + header.replace("\r", " ").replace("\n", " ") + "\n" + wrapped(cleaned, o.wrap))
    if not output:
        raise ValueError("No valid sequence records. " + " ".join(notices[:5]))
    (dest / "sequences.fasta").write_text("\n".join(output) + "\n", encoding="utf-8")
    (dest / "run.log").write_text("\n".join([f"Records: {len(output)}", *notices]) + "\n", encoding="utf-8")
