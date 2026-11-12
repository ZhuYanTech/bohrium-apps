def input_text(file, text):
    if bool(file) == bool(text.strip()):
        raise ValueError("Provide exactly one file or text input.")
    return file.read_text(encoding="utf-8-sig") if file else text


def option(value, allowed):
    if value not in allowed:
        raise ValueError(f"Expected one of {', '.join(sorted(allowed))}; got {value!r}.")
    return value
