#!/usr/bin/env python3
"""Inventaría CSV/JSON y detecta años visibles sin modificar datos originales."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw"
OUT = ROOT / "reports" / "file_inventory.csv"
YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")


def probe(path: Path) -> tuple[str, str, str]:
    years: set[int] = set()
    status = "ok"
    detail = ""
    try:
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            sample = json.dumps(obj, ensure_ascii=False)[:2_000_000]
        else:
            sample = path.read_text(encoding="utf-8-sig", errors="replace")[:2_000_000]
            # Confirm it is at least parseable as delimited text.
            next(csv.reader(sample.splitlines()))
        years = {int(y) for y in YEAR_RE.findall(sample)}
    except Exception as exc:  # validation report must survive individual bad files
        status, detail = "error", str(exc)
    visible = sorted(y for y in years if 1900 <= y <= 2100)
    return status, ";".join(map(str, visible)), detail


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(RAW.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".csv", ".json"}:
            status, years, detail = probe(path)
            rows.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "format": path.suffix.lower().lstrip("."),
                    "visible_years_sample": years,
                    "parse_status": status,
                    "detail": detail,
                }
            )
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["path"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} files -> {OUT}")


if __name__ == "__main__":
    main()
