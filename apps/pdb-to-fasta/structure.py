import re
from urllib.request import urlopen


def pdb_code(value):
    if not re.fullmatch(r"[0-9][A-Za-z0-9]{3}", value.strip()):
        raise ValueError("Expected a four-character PDB ID starting with a digit.")
    return value.strip().upper()


def get_structure(file, identifier, dest, extension="cif"):
    if bool(file) == bool(identifier.strip()):
        raise ValueError("Provide exactly one structure file or PDB ID.")
    if file:
        return file
    code = pdb_code(identifier)
    path = dest / f"{code}.{extension}"
    with urlopen(f"https://files.rcsb.org/download/{code}.{extension}", timeout=30) as response:
        data = response.read(50 * 1024**2 + 1)
    if len(data) > 50 * 1024**2:
        raise ValueError("Downloaded structure exceeds 50 MiB.")
    path.write_bytes(data)
    return path
