"""Registro de adaptadores.

Adaptadores públicos ficam neste pacote. Adaptadores privados podem ser
colocados em arquivos `*_local.py` (ignorados pelo Git) que definam
`NAME` (str) e `SOURCE` (classe); eles são carregados automaticamente.
"""
from __future__ import annotations

import importlib
import pkgutil

from .base import Chapter, Source
from .example import ExampleSource

REGISTRY: dict[str, type] = {"example": ExampleSource}

for _mod in pkgutil.iter_modules(__path__):
    if _mod.name.endswith("_local"):
        _m = importlib.import_module(f"{__name__}.{_mod.name}")
        REGISTRY[_m.NAME] = _m.SOURCE


def get_source(name: str, options: dict) -> Source:
    try:
        return REGISTRY[name](**options)
    except KeyError:
        known = ", ".join(sorted(REGISTRY)) or "nenhum"
        raise SystemExit(f"Adaptador '{name}' não implementado (disponíveis: {known}).")


__all__ = ["Chapter", "Source", "REGISTRY", "get_source"]
