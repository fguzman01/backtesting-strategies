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
