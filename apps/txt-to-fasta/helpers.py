def input_text(file, text):
    if bool(file) == bool(text.strip()):
        raise ValueError("Provide exactly one file or text input.")
    return file.read_text(encoding="utf-8-sig") if file else text


def fasta_records(text):
    records = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            name = line[1:].strip()
            if not name:
                raise ValueError("Empty FASTA header.")
            records.append((name, []))
        else:
            if not records:
                records.append(("Sequence", []))
            records[-1][1].append(line)
    return [(name, "\n".join(lines)) for name, lines in records]


def wrapped(sequence, width):
    if not 0 <= width <= 200:
        raise ValueError("Line width must be from 0 to 200.")
    return "\n".join(sequence[i:i + width] for i in range(0, len(sequence), width)) if width else sequence


def option(value, allowed):
    if value not in allowed:
        raise ValueError(f"Expected one of {', '.join(sorted(allowed))}; got {value!r}.")
    return value
