"""Holdout fijo.

Si se prueban veinte estrategias sobre los mismos datos y se elige la mejor, una se va a ver
excelente por azar. La protección es reservar un tramo que no se mira durante el desarrollo y
usarlo UNA vez sobre la candidata final. El corte es una constante (no relativo a hoy) y el default
es no verlo: cruzarlo hay que pedirlo. Mismo corte que btc-signal-web (`holdout.ts`).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

HOLDOUT_DESDE = pd.Timestamp("2025-09-09", tz="UTC")


@dataclass(frozen=True)
class Ventana:
    desde: pd.Timestamp
    hasta: pd.Timestamp
    tramo: str  # "desarrollo" | "holdout" | "mixto"
    aviso: str | None = None


def _ts(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def clasificar(desde, hasta) -> str:
    desde, hasta = _ts(desde), _ts(hasta)
    if hasta <= HOLDOUT_DESDE:
        return "desarrollo"
    if desde >= HOLDOUT_DESDE:
        return "holdout"
    return "mixto"


def resolver_ventana(desde, hasta, holdout: bool = False) -> Ventana:
    """Aplica la regla del holdout a una ventana pedida.

    - `holdout=False` (default): si la ventana cruza el corte se recorta en `HOLDOUT_DESDE`, con aviso.
      Recortar en silencio sería peor que fallar: daría un número correcto sobre otra ventana.
    - `holdout=True`: se respeta la ventana y se avisa que el holdout se mira una sola vez.
    """
    desde, hasta = _ts(desde), _ts(hasta)
    if desde >= hasta:
        raise ValueError(f"ventana vacía: {desde} → {hasta}")
    iso = HOLDOUT_DESDE.date().isoformat()
    if hasta <= HOLDOUT_DESDE:
        return Ventana(desde, hasta, "desarrollo")
    if holdout:
        return Ventana(
            desde,
            hasta,
            clasificar(desde, hasta),
            f"Incluye el holdout (desde {iso}). Se mira UNA vez, sobre la candidata final.",
        )
    if desde >= HOLDOUT_DESDE:
        raise ValueError(f"la ventana está entera en el holdout (desde {iso}): usar holdout=True")
    aviso = f"Ventana recortada en {iso} para no tocar el holdout."
    return Ventana(desde, HOLDOUT_DESDE, "desarrollo", aviso)
