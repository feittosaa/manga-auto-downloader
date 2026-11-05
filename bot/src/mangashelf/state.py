"""Estado de downloads em SQLite."""
from __future__ import annotations

import sqlite3
import time
from decimal import Decimal
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
    series TEXT NOT NULL,
    number TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    updated_at REAL NOT NULL,
    PRIMARY KEY (series, number)
)
"""
STATUSES = ("pending", "done", "failed")


class State:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(SCHEMA)
        self.db.commit()

    def upsert(self, series: str, number: Decimal, url: str) -> None:
        self.db.execute(
            "INSERT INTO chapters (series, number, url, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(series, number) DO UPDATE SET url=excluded.url",
            (series, str(number), url, time.time()),
        )
        self.db.commit()

    def mark(self, series: str, number: Decimal, status: str, error: str | None = None) -> None:
        assert status in STATUSES
        self.db.execute(
            "UPDATE chapters SET status=?, error=?, updated_at=? WHERE series=? AND number=?",
            (status, error, time.time(), series, str(number)),
        )
        self.db.commit()

    def counts(self, series: str) -> dict[str, int]:
        rows = self.db.execute(
            "SELECT status, COUNT(*) FROM chapters WHERE series=? GROUP BY status", (series,)
        ).fetchall()
        return {s: 0 for s in STATUSES} | dict(rows)

    def failed(self, series: str) -> list[tuple[Decimal, str]]:
        rows = self.db.execute(
            "SELECT number, COALESCE(error,'') FROM chapters WHERE series=? AND status='failed'",
            (series,),
        ).fetchall()
        return sorted((Decimal(n), e) for n, e in rows)
