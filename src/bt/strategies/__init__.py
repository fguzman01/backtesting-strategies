"""Estrategias: un módulo por estrategia con una función `senales(df, **params) -> DataFrame`.

Ver el contrato de columnas en `bt.engine`. Todo módulo nuevo necesita un test que pase
`bt.checks.chequear_lookahead`.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable

import pandas as pd

Estrategia = Callable[..., pd.DataFrame]


def cargar(nombre: str) -> Estrategia:
    if not nombre.isidentifier():
        raise ValueError(f"nombre de estrategia inválido: {nombre!r}")
    mod = importlib.import_module(f"bt.strategies.{nombre}")
    return mod.senales


def es_corte(nombre: str) -> bool:
    """¿Es una estrategia de corte transversal (`CORTE_TRANSVERSAL = True`, `senales_corte`)?"""
    if not nombre.isidentifier():
        raise ValueError(f"nombre de estrategia inválido: {nombre!r}")
    return bool(getattr(importlib.import_module(f"bt.strategies.{nombre}"), "CORTE_TRANSVERSAL", False))


def cargar_corte(nombre: str) -> Callable[..., dict[str, pd.DataFrame]]:
    """`senales_corte(velas, miembros, **params) -> {símbolo: DataFrame de señales}`."""
    if not es_corte(nombre):
        raise ValueError(f"`{nombre}` no es una estrategia de corte transversal")
    return importlib.import_module(f"bt.strategies.{nombre}").senales_corte
