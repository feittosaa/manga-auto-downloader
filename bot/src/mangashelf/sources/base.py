"""Contrato dos adaptadores de fonte."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Chapter:
    number: Decimal
    url: str


USER_AGENT = "mangashelf/0.1 (uso pessoal)"


class Source(Protocol):
    def discover(self, series: str) -> list[Chapter]:
        """Lista capítulos e seus links de download."""
        ...
