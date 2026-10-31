"""PennyLab advanced CSV join challenge — standard-library implementation."""
import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

def merge_csvs(left_path: str, right_path: str, key_col: str, output_path: str) -> None:
    """Stable many-to-many inner join. Right non-key collisions gain _right suffixes.
    Empty join keys do not match. UTF-8 BOM is accepted. Output is atomically replaced.
    """
    output = Path(output_path)
    with open(left_path, newline="", encoding="utf-8-sig") as lf, open(right_path, newline="", encoding="utf-8-sig") as rf:
        left = csv.DictReader(lf, strict=True)
        right = csv.DictReader(rf, strict=True)
        a, b = left.fieldnames, right.fieldnames
        if not a or not b or key_col not in a or key_col not in b:
            raise ValueError("both CSVs require headers containing the join key")
        if len(set(a)) != len(a) or len(set(b)) != len(b):
            raise ValueError("duplicate input column names")
        names = list(a)
        rightcols = [x for x in b if x != key_col]
        mapping = {}
        for col in rightcols:
            target = col
            if target in names:
                target = col + "_right"
                while target in names or target in mapping.values():
                    target += "_right"
            names.append(target)
            mapping[col] = target
        lookup = {}
        for row in right:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("ragged CSV row")
            k = row[key_col]
            if k != "":
                lookup.setdefault(k, []).append(row)
        output.parent.mkdir(parents=True, exist_ok=True)
        tempname = None
        try:
            with NamedTemporaryFile("w", newline="", encoding="utf-8", dir=output.parent, delete=False) as tmp:
                tempname = tmp.name
                writer = csv.DictWriter(tmp, fieldnames=names, lineterminator="\n")
                writer.writeheader()
                for row in left:
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError("ragged CSV row")
                    for rr in lookup.get(row[key_col], ()) if row[key_col] != "" else ():
                        writer.writerow({**row, **{mapping[k]: rr[k] for k in rightcols}})
            os.replace(tempname, output)
        finally:
            if tempname and os.path.exists(tempname):
                os.unlink(tempname)
