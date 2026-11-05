"""Organização da biblioteca em disco."""
from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

_NAME_RE = re.compile(r"^Capitulo_(\d+(?:\.\d+)?)\.cbz$")


def format_number(number: Decimal) -> str:
    """1 -> '001', 1.5 -> '001.5'."""
    whole, _, frac = f"{number:f}".partition(".")
    frac = frac.rstrip("0")
    return f"{int(whole):03d}" + (f".{frac}" if frac else "")


def chapter_filename(number: Decimal) -> str:
    return f"Capitulo_{format_number(number)}.cbz"


def series_dir(library: Path, series: str) -> Path:
    safe = re.sub(r'[\\/:*?"<>|]', "_", series).strip() or "serie"
    return library / safe


def list_chapters(directory: Path) -> list[tuple[Decimal, Path]]:
    """Capítulos existentes, ordenados numericamente."""
    found = []
    for p in directory.glob("Capitulo_*.cbz") if directory.is_dir() else []:
        m = _NAME_RE.match(p.name)
        if m:
            found.append((Decimal(m.group(1)), p))
    return sorted(found)


def find_gaps(numbers: list[Decimal]) -> list[int]:
    """Números inteiros ausentes entre o menor e o maior capítulo."""
    ints = {int(n) for n in numbers}
    if not ints:
        return []
    return [i for i in range(min(ints), max(ints) + 1) if i not in ints]
