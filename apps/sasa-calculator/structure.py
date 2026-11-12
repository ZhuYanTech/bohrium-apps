import re
from urllib.request import urlopen
from pathlib import Path
from zipfile import ZipFile

STRUCTURE_EXTENSIONS = {".pdb", ".ent", ".cif", ".mmcif", ".pdbx"}


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


def structure_files(path, root):
    if path.suffix.lower() != ".zip":
        return [path]
    root.mkdir(exist_ok=True)
    output = []
    with ZipFile(path) as archive:
        for member in archive.infolist():
            filename = Path(member.filename)
            if member.is_dir() or filename.name.startswith(".") or "__MACOSX" in filename.parts:
                continue
            if filename.suffix.lower() not in STRUCTURE_EXTENSIONS:
                raise ValueError(f"Unsupported ZIP member: {filename.name}")
            if len(output) >= 20 or member.file_size > 50 * 1024**2:
                raise ValueError("ZIP accepts up to 20 files, up to 50 MiB each.")
            target = root / f"{len(output)+1}_{filename.name}"
            target.write_bytes(archive.read(member))
            output.append(target)
    if not output:
        raise ValueError("No structure files in ZIP.")
    return output


def read_structure(path):
    from Bio.PDB import MMCIFParser, PDBParser

    if path.stat().st_size > 50 * 1024**2:
        raise ValueError("Structure exceeds 50 MiB.")
    parser = MMCIFParser(QUIET=True) if path.suffix.lower() in {".cif",".mmcif",".pdbx"} else PDBParser(QUIET=True)
    return parser.get_structure(path.stem, str(path))
