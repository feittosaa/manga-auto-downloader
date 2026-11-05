"""CLI do MangaShelf."""
from __future__ import annotations

import argparse
import logging
import time
from decimal import Decimal
from pathlib import Path

import httpx

from .archive import validate_cbz
from .config import load_source
from .sources.base import USER_AGENT
from .downloader import DownloadError, download_cbz
from .library import chapter_filename, find_gaps, list_chapters, series_dir
from .sources import get_source
from .state import State

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "sources.yaml"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mangashelf")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("discover", "download", "verify", "status"):
        s = sub.add_parser(name)
        s.add_argument("--source", required=name in ("discover", "download"))
        s.add_argument("--series", required=True)
        if name == "download":
            s.add_argument("--from", dest="start", type=Decimal)
            s.add_argument("--to", dest="end", type=Decimal)
    return p


def _in_range(n: Decimal, start: Decimal | None, end: Decimal | None) -> bool:
    return (start is None or n >= start) and (end is None or n <= end)


def cmd_discover(args) -> int:
    cfg = load_source(args.config, args.source)
    for ch in sorted(get_source(cfg.adapter or cfg.name, {"base_url": cfg.base_url}).discover(args.series), key=lambda c: c.number):
        print(f"{ch.number}\t{ch.url}")
    return 0


def cmd_download(args) -> int:
    cfg = load_source(args.config, args.source)
    source = get_source(cfg.adapter or cfg.name, {"base_url": cfg.base_url})
    state = State(cfg.state_dir / "state.db")
    out = series_dir(cfg.library_dir, (cfg.series_names or {}).get(args.series, args.series))
    chapters = [c for c in source.discover(args.series) if _in_range(c.number, args.start, args.end)]
    chapters.sort(key=lambda c: c.number)
    for c in chapters:
        state.upsert(args.series, c.number, c.url)
    failures = 0
    with httpx.Client(timeout=cfg.timeout_seconds, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for c in chapters:
            dest = out / chapter_filename(c.number)
            if dest.exists() and validate_cbz(dest)[0]:
                state.mark(args.series, c.number, "done")
                print(f"existe {c.number}")
                continue
            try:
                download_cbz(client, c.url, dest, cfg.downloads_dir, cfg.max_retries, cfg.backoff_seconds)
                state.mark(args.series, c.number, "done")
                print(f"ok     {c.number}")
            except DownloadError as e:
                failures += 1
                state.mark(args.series, c.number, "failed", str(e))
                print(f"falhou {c.number}: {e}")
            time.sleep(cfg.delay_seconds)
    print(f"{len(chapters) - failures} ok, {failures} falhas")
    return 1 if failures else 0


def cmd_verify(args) -> int:
    cfg = load_source(args.config, args.source) if args.source else None
    library = cfg.library_dir if cfg else DEFAULT_CONFIG.parents[1] / "data" / "library"
    chapters = list_chapters(series_dir(library, args.series))
    bad = 0
    for n, path in chapters:
        ok, reason = validate_cbz(path)
        if not ok:
            bad += 1
            print(f"inválido {path.name}: {reason}")
    gaps = find_gaps([n for n, _ in chapters])
    print(f"{len(chapters)} capítulos, {bad} inválidos, lacunas: {gaps or 'nenhuma'}")
    return 1 if bad else 0


def cmd_status(args) -> int:
    base = DEFAULT_CONFIG.parents[1] / "data" / "state" / "state.db"
    state = State(base)
    counts = state.counts(args.series)
    print(", ".join(f"{k}: {v}" for k, v in counts.items()))
    for n, err in state.failed(args.series):
        print(f"  falhou {n}: {err}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    return {"discover": cmd_discover, "download": cmd_download, "verify": cmd_verify, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
