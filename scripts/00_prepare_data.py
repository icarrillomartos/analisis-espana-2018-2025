#!/usr/bin/env python3
"""Restaura datasets comprimidos que exceden el límite por fichero de GitHub."""

from __future__ import annotations

import gzip
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data_raw/demografia_economia/ine_70364_2018_2025.json"
ARCHIVE = TARGET.with_suffix(TARGET.suffix + ".gz")


def main() -> None:
    if TARGET.exists():
        print(f"Ya existe: {TARGET}")
        return
    if not ARCHIVE.exists():
        raise FileNotFoundError(f"No existe el original ni su archivo comprimido: {ARCHIVE}")
    with gzip.open(ARCHIVE, "rb") as source, TARGET.open("wb") as destination:
        shutil.copyfileobj(source, destination)
    print(f"Restaurado: {TARGET}")


if __name__ == "__main__":
    main()
