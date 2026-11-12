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


def option(value, allowed):
    if value not in allowed:
        raise ValueError(f"Expected one of {', '.join(sorted(allowed))}; got {value!r}.")
    return value
