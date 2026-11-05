"""Validação de arquivos CBZ."""
from __future__ import annotations

import zipfile
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".jpe", ".png", ".webp", ".gif", ".avif", ".bmp"}


def validate_cbz(path: Path) -> tuple[bool, str]:
    """Retorna (ok, motivo). Verifica: existe, não vazio, ZIP legível, contém imagens."""
    if not path.is_file():
        return False, "arquivo inexistente"
    if path.stat().st_size == 0:
        return False, "arquivo vazio"
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                return False, f"entrada corrompida: {bad}"
            images = [n for n in zf.namelist() if Path(n).suffix.lower() in IMAGE_EXTS]
    except zipfile.BadZipFile:
        return False, "ZIP inválido"
    if not images:
        return False, "nenhuma imagem no arquivo"
    return True, "ok"
