"""Resolve ordered ZIP input groups and numeric CSV pairings for PoseBusters."""

import csv
from io import StringIO
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

GROUPS = ("mol_pred", "mol_true", "mol_cond")
FORMATS = {".sdf", ".mol", ".mol2", ".pdb"}
LIMIT = 50 * 1024**2


def load_bundle(bundle: Path, workspace: Path, pairing: str = "") -> list[dict[str, Path]]:
    groups: dict[str, list[Path]] = {name: [] for name in GROUPS}
    seen = set()
    with ZipFile(bundle) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            path = PurePosixPath(entry.filename)
            if path.parts[0] == "__MACOSX" or path.name == ".DS_Store":
                continue
            if entry.file_size > LIMIT:
                raise ValueError(f"{entry.filename} 超过 50 MiB。")
            if entry.filename == "pairs.csv":
                if pairing:
                    raise ValueError("请只提供一份 CSV 配对表。")
                pairing = archive.read(entry).decode("utf-8-sig")
                continue
            if len(path.parts) != 2 or path.parts[0] not in GROUPS or path.suffix.lower() not in FORMATS:
                raise ValueError(f"无法识别压缩包条目：{entry.filename}")
            if entry.filename in seen:
                raise ValueError(f"压缩包含重复文件：{entry.filename}")
            seen.add(entry.filename)
            group = groups[path.parts[0]]
            if len(group) >= 20:
                raise ValueError("每个文件组最多 20 个文件。")
            # Use generated paths. ZIP member names never become extraction paths.
            dest = workspace / path.parts[0] / str(len(group) + 1) / (path.stem + path.suffix.lower())
            dest.parent.mkdir(parents=True)
            dest.write_bytes(archive.read(entry))
            group.append(dest)

    if not groups["mol_pred"]:
        raise ValueError("压缩包需要至少一个 mol_pred/ 姿势文件。")
    if not pairing.strip():
        if len(groups["mol_true"]) > 1 or len(groups["mol_cond"]) > 1:
            raise ValueError("使用多个参考或受体时需要 pairs.csv。")
        shared = {key: paths[0] for key, paths in groups.items() if key != "mol_pred" and paths}
        return [{"mol_pred": pose, **shared} for pose in groups["mol_pred"]]

    reader = csv.DictReader(StringIO(pairing.strip()), strict=True)
    if not reader.fieldnames or "mol_pred" not in reader.fieldnames or set(reader.fieldnames) - set(GROUPS):
        raise ValueError("配对表需要 mol_pred 列，可选 mol_true 和 mol_cond 列。")
    rows = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"配对表第 {reader.line_num} 行列数不匹配。")
        pairs = {}
        for key, raw in row.items():
            value = raw.strip()
            if not value and key != "mol_pred":
                continue
            if not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= len(groups[key]):
                raise ValueError(f"配对表第 {reader.line_num} 行 {key} 编号无效。")
            pairs[key] = groups[key][int(value) - 1]
        rows.append(pairs)
    if not rows:
        raise ValueError("CSV 配对表没有数据行。")
    return rows
