"""Simulador por barras.

Contrato con las estrategias (`bt.strategies`): `senales(df, **params)` devuelve un DataFrame con el
mismo índice que `df` y estas columnas, calculadas SÓLO con datos hasta el cierre de cada vela:

- `direccion`: +1 largo, −1 corto, 0 nada. Se ejecuta en la APERTURA de la vela siguiente.
- `stop`: precio del stop (obligatorio cuando `direccion != 0`).
- `objetivo` (opcional): precio objetivo. Si falta y `Config.objetivo_r` está, se usa
  entrada ± objetivo_r × riesgo.
- `salida` (opcional, bool): cerrar la posición abierta en la apertura de la vela siguiente
  (salidas por regla, p. ej. Donchian de 10).

Una posición a la vez. Dos modelos de llenado para lo que no se sabe dentro de una vela
(ver 02-DOCS/reglas-de-medicion.md): `conservador` (el adverso primero, el que se reporta) y
`optimista`. El deslizamiento mueve sólo el precio de entrada; NO filtra operaciones (la confusión
compuerta/llenado sesgó a btc-signal-web hasta el 2026-10-11).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

MOTIVOS_RESUELTOS = frozenset({"SL", "TP", "TIMEOUT", "SALIDA"})


@dataclass(frozen=True)
class Config:
    fee_pct_por_lado: float = 0.0005
    deslizamiento_pct: float = 0.0
    timeout_velas: int | None = None
    objetivo_r: float | None = None

    def como_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trade:
    direccion: int
    senal_en: str
    abierto_en: str
    cerrado_en: str | None
    entrada: float
    stop: float
    objetivo: float | None
    salida: float | None
    motivo: str  # SL | TP | TIMEOUT | SALIDA | SIN_RESOLVER | STOP_INVALIDO
    r_bruto: float
    fee_r: float
    r_neto: float
    mae_r: float
    velas: int

    @property
    def resuelto(self) -> bool:
        return self.motivo in MOTIVOS_RESUELTOS


def _col(sen: pd.DataFrame, nombre: str, defecto) -> np.ndarray:
    if nombre in sen:
        return sen[nombre].to_numpy()
    return np.full(len(sen), defecto)


def simular(df: pd.DataFrame, sen: pd.DataFrame, cfg: Config, modelo: str = "conservador") -> list[Trade]:
    if modelo not in ("conservador", "optimista"):
        raise ValueError(modelo)
    if not sen.index.equals(df.index):
        raise ValueError("las señales deben tener el mismo índice que las velas")

    o, h, lo, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    t = df.index
    direc = np.nan_to_num(_col(sen, "direccion", 0).astype(float)).astype(int)
    stops = _col(sen, "stop", np.nan).astype(float)
    objs = _col(sen, "objetivo", np.nan).astype(float)
    salidas = _col(sen, "salida", False).astype(bool)
    adverso_primero = modelo == "conservador"
    n = len(df)
    trades: list[Trade] = []

    i = 0
    while i < n - 1:
        d = direc[i]
        if d == 0 or not math.isfinite(stops[i]):
            i += 1
            continue
        j = i + 1
        entrada = o[j] * (1 + d * cfg.deslizamiento_pct)
        stop = stops[i]
        riesgo = (entrada - stop) * d
        if riesgo <= 0:
            trades.append(_trade(d, t[i], t[j], None, entrada, stop, None, None, "STOP_INVALIDO", 0, 0, 0, 0))
            i += 1
            continue
        obj = objs[i] if math.isfinite(objs[i]) else None
        if obj is None and cfg.objetivo_r:
            obj = entrada + d * cfg.objetivo_r * riesgo
        fee_r = cfg.fee_pct_por_lado * 2 * entrada / riesgo

        peor = entrada
        salida = motivo = None
        k = j
        while k < n:
            # Gap: la vela abre ya pasada del stop/objetivo (no aplica a la vela de entrada).
            if k > j:
                if (o[k] - stop) * d <= 0:
                    salida, motivo = o[k], "SL"
                elif obj is not None and (o[k] - obj) * d >= 0:
                    salida, motivo = o[k], "TP"
                if motivo:
                    peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
                    break
            peor = min(peor, lo[k]) if d > 0 else max(peor, h[k])
            toca_stop = (lo[k] if d > 0 else h[k]) * d <= stop * d
            toca_obj = obj is not None and (h[k] if d > 0 else lo[k]) * d >= obj * d
            if toca_stop and toca_obj:
                salida, motivo = (stop, "SL") if adverso_primero else (obj, "TP")
            elif toca_stop:
                salida, motivo = stop, "SL"
            elif toca_obj:
                salida, motivo = obj, "TP"
            elif cfg.timeout_velas and k - j + 1 >= cfg.timeout_velas:
                salida, motivo = c[k], "TIMEOUT"
            elif salidas[k] and k + 1 < n:
                k += 1
                salida, motivo = o[k], "SALIDA"
                peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
            if motivo:
                break
            k += 1

        if motivo is None:
            trades.append(
                _trade(d, t[i], t[j], None, entrada, stop, obj, None, "SIN_RESOLVER", 0, fee_r, 0, n - j)
            )
            break
        r_bruto = (salida - entrada) * d / riesgo
        mae_r = max(0.0, (entrada - peor) * d / riesgo)
        trades.append(
            _trade(d, t[i], t[j], t[k], entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, k - j + 1)
        )
        # La vela de salida puede generar una señal nueva (se ejecutaría en la siguiente).
        i = k
    return trades


def _trade(d, ts, ta, tc, entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, velas) -> Trade:
    resuelto = motivo in MOTIVOS_RESUELTOS
    return Trade(
        direccion=int(d),
        senal_en=ts.isoformat(),
        abierto_en=ta.isoformat(),
        cerrado_en=tc.isoformat() if tc is not None else None,
        entrada=float(entrada),
        stop=float(stop),
        objetivo=float(obj) if obj is not None else None,
        salida=float(salida) if salida is not None else None,
        motivo=motivo,
        r_bruto=float(r_bruto),
        fee_r=float(fee_r),
        r_neto=float(r_bruto - fee_r) if resuelto else 0.0,
        mae_r=float(mae_r),
        velas=int(velas),
    )


def simular_ambos(df: pd.DataFrame, sen: pd.DataFrame, cfg: Config) -> dict[str, list[Trade]]:
    return {m: simular(df, sen, cfg, m) for m in ("conservador", "optimista")}
