"""Chequeos anti-sesgo deterministas. Son el "revisor" que no tiene sesgo de autor."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from bt.engine import Config, simular_ambos


def chequear_lookahead(
    senales: Callable[..., pd.DataFrame], df: pd.DataFrame, cortes: int = 5, **params
) -> list[str]:
    """Calcula las señales con toda la historia y con la historia cortada en varios puntos.

    Si la señal de la vela `t` cambia según haya o no velas después de `t`, la estrategia mira el
    futuro. Devuelve la lista de problemas (vacía = pasa).
    """
    completo = senales(df, **params)
    problemas: list[str] = []
    n = len(df)
    for pos in np.linspace(n // 3, n - 2, cortes).astype(int):
        parcial = senales(df.iloc[: pos + 1], **params)
        a = completo.iloc[: pos + 1]
        for col in parcial.columns:
            x, y = a[col].to_numpy(), parcial[col].to_numpy()
            if x.dtype.kind == "f" or y.dtype.kind == "f":
                igual = np.isclose(x.astype(float), y.astype(float), equal_nan=True, rtol=1e-9, atol=1e-12)
            else:
                igual = x == y
            if not igual.all():
                primera = df.index[int(np.argmin(igual))]
                problemas.append(f"look-ahead en '{col}': cambia en {primera} al cortar en {df.index[pos]}")
    return problemas


def chequear_lookahead_corte(
    senales_corte: Callable[..., dict[str, pd.DataFrame]], velas: dict[str, pd.DataFrame],
    miembros: dict[str, list[str]] | None = None, cortes: int = 5, **params
) -> list[str]:
    """Como `chequear_lookahead`, pero con todos los símbolos: las señales de cada símbolo en `t` no
    pueden cambiar según haya o no velas posteriores a `t` (en ningún símbolo)."""
    from bt.run import alinear

    alineadas = alinear(velas)
    completo = senales_corte(alineadas, miembros, **params)
    indice = next(iter(alineadas.values())).index
    problemas: list[str] = []
    for pos in np.linspace(len(indice) // 3, len(indice) - 2, cortes).astype(int):
        parcial = senales_corte({s: d.iloc[: pos + 1] for s, d in alineadas.items()}, miembros, **params)
        for s, p in parcial.items():
            a = completo[s].iloc[: pos + 1]
            for col in p.columns:
                x, y = a[col].to_numpy(), p[col].to_numpy()
                if x.dtype.kind == "f" or y.dtype.kind == "f":
                    igual = np.isclose(x.astype(float), y.astype(float), equal_nan=True, rtol=1e-9, atol=1e-12)
                else:
                    igual = x == y
                if not igual.all():
                    problemas.append(
                        f"look-ahead en {s}/'{col}': cambia en {indice[int(np.argmin(igual))]} "
                        f"al cortar en {indice[pos]}"
                    )
    return problemas


def chequear_determinismo(
    senales: Callable[..., pd.DataFrame], df: pd.DataFrame, cfg: Config, **params
) -> list[str]:
    """Dos corridas idénticas deben dar trades idénticos."""
    a = simular_ambos(df, senales(df, **params), cfg)
    b = simular_ambos(df, senales(df, **params), cfg)
    return [] if a == b else ["dos corridas idénticas dieron trades distintos"]


def chequear_comision(cfg: Config) -> list[str]:
    return [] if cfg.fee_pct_por_lado > 0 else ["la corrida no aplica comisión"]
