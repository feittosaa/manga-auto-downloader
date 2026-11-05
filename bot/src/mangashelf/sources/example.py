"""Adaptador de exemplo: lê um índice JSON que você mesmo publica ou mantém.

Formato esperado em `{base_url}/{series}.json`:
    {"chapters": [{"number": 1, "url": "https://.../cap-001.cbz"}, ...]}
"""
from __future__ import annotations

from decimal import Decimal

import httpx

from .base import USER_AGENT, Chapter


class ExampleSource:
    def __init__(self, base_url: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(
            timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True
        )

    def discover(self, series: str) -> list[Chapter]:
        r = self.client.get(f"{self.base_url}/{series}.json")
        r.raise_for_status()
        return [
            Chapter(number=Decimal(str(c["number"])), url=c["url"])
            for c in r.json()["chapters"]
        ]
