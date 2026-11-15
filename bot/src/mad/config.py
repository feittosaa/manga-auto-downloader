"""Carregamento de configuração das fontes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SourceConfig:
    name: str
    base_url: str
    library_dir: Path
    downloads_dir: Path
    state_dir: Path
    concurrency: int = 1
    timeout_seconds: float = 30
    max_retries: int = 5
    backoff_seconds: float = 2
    delay_seconds: float = 1
    adapter: str = ""
    series_names: dict[str, str] | None = None  # slug -> nome da pasta


def load_source(config_path: Path, name: str) -> SourceConfig:
    if not config_path.is_file():
        raise SystemExit(f"Config não encontrada: {config_path} (copie sources.example.yaml)")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw = (data.get("sources") or {}).get(name)
    if raw is None:
        raise SystemExit(f"Fonte '{name}' não definida em {config_path}")
    base = config_path.parent.parent  # raiz do projeto
    paths = {k: base / raw.pop(k) for k in ("library_dir", "downloads_dir", "state_dir")}
    return SourceConfig(name=name, **paths, **raw)
