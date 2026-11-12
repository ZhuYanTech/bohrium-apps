def input_text(file, text):
    if bool(file) == bool(text.strip()):
        raise ValueError("Provide exactly one file or text input.")
    return file.read_text(encoding="utf-8-sig") if file else text
