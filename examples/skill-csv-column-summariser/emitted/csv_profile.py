#!/usr/bin/env python3
"""Deterministic per-column profile of a CSV (standard library only).

Companion to the csv-column-summarise skill: the skill runs this to get the numbers,
then adds a plain-English interpretation. Type-hinted so a static checker (mypy) can
guard the type & value discipline (the numeric mean stays a float; counts stay int).
"""
from __future__ import annotations

import csv
import json
import sys
from typing import Any, Final

SAMPLE_LIMIT: Final[int] = 3


def _is_int(s: str) -> bool:
    try:
        int(s)
    except ValueError:
        return False
    return True


def _is_float(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


def profile(path: str) -> dict[str, Any]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header: list[str] = next(reader)
        except StopIteration:
            return {"rows": 0, "columns": []}
        cols: list[list[str]] = [[] for _ in header]
        rows: int = 0
        for row in reader:
            if len(row) != len(header):
                continue  # skip malformed row
            rows += 1
            for i, val in enumerate(row):
                cols[i].append(val)

    out: list[dict[str, Any]] = []
    for name, values in zip(header, cols):
        nonnull: list[str] = [v for v in values if v != ""]
        fill_rate: float = (len(nonnull) / rows) if rows else 0.0
        col: dict[str, Any] = {
            "name": name,
            "fill_rate": round(fill_rate, 4),
            "cardinality": len(set(nonnull)),
            "samples": nonnull[:SAMPLE_LIMIT],
        }
        if not nonnull:
            col["type"] = "empty"
        elif all(_is_int(v) for v in nonnull):
            ints: list[int] = [int(v) for v in nonnull]
            col["type"] = "int"
            col["min"], col["max"] = min(ints), max(ints)
            col["mean"] = float(sum(ints)) / len(ints)  # mean stays float
        elif all(_is_float(v) for v in nonnull):
            floats: list[float] = [float(v) for v in nonnull]
            col["type"] = "float"
            col["min"], col["max"] = min(floats), max(floats)
            col["mean"] = sum(floats) / len(floats)
        else:
            col["type"] = "string"
        out.append(col)
    return {"rows": rows, "columns": out}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python csv_profile.py <path.csv>", file=sys.stderr)
        return 2
    print(json.dumps(profile(argv[1]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
