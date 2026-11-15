"""Download de CBZ com arquivo temporário, retentativas e validação."""
from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path

import httpx

from .archive import validate_cbz

log = logging.getLogger(__name__)
RETRY_STATUS = {429, 500, 502, 503, 504}


class DownloadError(Exception):
    pass


def download_cbz(
    client: httpx.Client,
    url: str,
    dest: Path,
    tmp_dir: Path,
    max_retries: int = 5,
    backoff: float = 2.0,
) -> None:
    """Baixa para `.part`, valida e só então move para `dest`. Nunca sobrescreve CBZ válido."""
    if dest.exists() and validate_cbz(dest)[0]:
        return
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = tmp_dir / (dest.name + ".part")
    last = "desconhecido"
    for attempt in range(max_retries + 1):
        if attempt:
            wait = backoff * 2 ** (attempt - 1)
            log.warning("Tentativa %d/%d em %.1fs (%s)", attempt, max_retries, wait, last)
            time.sleep(wait)
        try:
            with client.stream("GET", url) as r:
                if r.status_code in RETRY_STATUS:
                    last = f"HTTP {r.status_code}"
                    continue
                r.raise_for_status()
                with part.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        except httpx.HTTPStatusError as e:
            raise DownloadError(f"HTTP {e.response.status_code}") from e
        except httpx.TransportError as e:
            last = str(e) or type(e).__name__
            continue
        ok, reason = validate_cbz(part)
        if not ok:
            part.unlink(missing_ok=True)
            last = f"CBZ inválido: {reason}"
            continue
        _move(part, dest)
        return
    raise DownloadError(last)


def _move(src: Path, dest: Path) -> None:
    """Move entre dispositivos de forma atômica no destino (copia para .part e renomeia)."""
    try:
        os.replace(src, dest)
    except OSError:
        staging = dest.with_name(dest.name + ".part")
        shutil.copyfile(src, staging)
        os.replace(staging, dest)
        src.unlink()
