"""Simulador por barras.

Contrato con las estrategias (`bt.strategies`): `senales(df, **params)` devuelve un DataFrame con el
mismo índice que `df` y estas columnas, calculadas SÓLO con datos hasta el cierre de cada vela:

- `direccion`: +1 largo, −1 corto, 0 nada. Se ejecuta en la APERTURA de la vela siguiente.
- `stop`: precio del stop; o bien
- `riesgo`: distancia del stop medida desde la entrada REAL (stop = entrada − dirección × riesgo).
  Si están las dos, manda `riesgo`.
- `objetivo` (opcional): precio objetivo. Si falta y `Config.objetivo_r` está, se usa
  entrada ± objetivo_r × riesgo.
- `salida` (opcional, bool): cerrar la posición abierta en la apertura de la vela siguiente
  (salidas por regla, p. ej. el canal corto de Donchian). Si la salida depende del lado, usar
  `salida_largo` / `salida_corto`, que mandan sobre `salida` para su lado.
- `trailing` (opcional): distancia del trailing stop en precio (p. ej. 3 × ATR). Al cierre de cada
  vela con la posición abierta, el stop pasa a `mejor precio DESDE LA ENTRADA − dirección × trailing`
  si eso lo acerca; rige desde la vela siguiente. Nunca se aleja.

Gestión de la posición en `Config` (como el bot real; todo apagado por defecto):

- `breakeven_r`: cuando el precio llegó a entrada + breakeven_r × riesgo, el stop pasa a la entrada
  (desde la vela siguiente).
- `tp1_r` + `tp1_cierre`: en entrada + tp1_r × riesgo se cierra la fracción `tp1_cierre`; el resto
  sigue con el stop en breakeven (desde la vela siguiente) hacia el `objetivo`, el trailing, la regla
  o el timeout. Con `tp1_cierre = 1` es simplemente un objetivo.

Una posición a la vez. Dos modelos de llenado para lo que no se sabe dentro de una vela
(ver 02-DOCS/reglas-de-medicion.md): `conservador` (el adverso primero, el que se reporta) y
`optimista`. El deslizamiento mueve sólo el precio de entrada; NO filtra operaciones (la confusión
compuerta/llenado sesgó a btc-signal-web hasta el 2026-10-11). Todo ajuste del stop (trailing,
breakeven) se decide con la vela cerrada y rige desde la siguiente: dentro de una vela no se sabe en
qué orden pasaron el máximo y el mínimo.

Funding (futuros perpetuos): se le cobra al trade la suma de las tasas con instante en
(apertura, cierre], con signo según la dirección. El instante del cierre sigue esta convención,
la misma de btc-signal-web: salida a la apertura de una vela → esa apertura; stop/objetivo dentro
de la vela → mitad de la vela; salida al cierre → fin de la vela.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

MOTIVOS_RESUELTOS = frozenset({"SL", "TP", "TIMEOUT", "SALIDA", "FIN"})


def es_resuelto(motivo: str) -> bool:
    """`TP1+SL`, `TP1+TP`, ...: una salida parcial seguida de la final cuenta por la final."""
    return motivo.split("+")[-1] in MOTIVOS_RESUELTOS


@dataclass(frozen=True)
class Config:
    fee_pct_por_lado: float = 0.0005
    deslizamiento_pct: float = 0.0
    timeout_velas: int | None = None
    objetivo_r: float | None = None
    # Una posición abierta al terminar los datos se cierra al último cierre (motivo FIN) y cuenta.
    # Si es False queda SIN_RESOLVER y no cuenta (lo que hace el motor TS de btc-signal-web).
    cerrar_al_final: bool = False
    breakeven_r: float | None = None
    tp1_r: float | None = None
    tp1_cierre: float = 1.0

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
    motivo: str  # SL | TP | TIMEOUT | SALIDA | FIN | TP1+<final> | SIN_RESOLVER | STOP_INVALIDO
    r_bruto: float
    fee_r: float
    r_neto: float
    mae_r: float
    velas: int
    funding_r: float = 0.0

    @property
    def resuelto(self) -> bool:
        return es_resuelto(self.motivo)


def _col(sen: pd.DataFrame, nombre: str, defecto) -> np.ndarray:
    if nombre in sen:
        return sen[nombre].to_numpy()
    return np.full(len(sen), defecto)


class _Funding:
    """Suma de tasas de funding con instante en (a, b], en ms."""

    def __init__(self, serie: pd.Series | None):
        self.ts = None
        if serie is None or len(serie) == 0:
            return
        s = serie.sort_index()
        idx = pd.DatetimeIndex(s.index)
        idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
        self.ts = idx.as_unit("ms").asi8
        self.acum = np.concatenate([[0.0], np.cumsum(s.to_numpy(dtype=float))])

    def entre(self, a_ms: int, b_ms: int) -> float:
        if self.ts is None:
            return 0.0
        hasta = self.acum[np.searchsorted(self.ts, b_ms, "right")]
        return float(hasta - self.acum[np.searchsorted(self.ts, a_ms, "right")])


def simular(
    df: pd.DataFrame, sen: pd.DataFrame, cfg: Config, modelo: str = "conservador",
    funding: pd.Series | None = None,
) -> list[Trade]:
    if modelo not in ("conservador", "optimista"):
        raise ValueError(modelo)
    if not sen.index.equals(df.index):
        raise ValueError("las señales deben tener el mismo índice que las velas")
    if not 0 < cfg.tp1_cierre <= 1:
        raise ValueError("tp1_cierre tiene que estar en (0, 1]")

    o, h, lo, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    t = df.index
    t_ms = pd.DatetimeIndex(t).as_unit("ms").asi8
    paso = int(np.median(np.diff(t_ms))) if len(t) > 1 else 0
    direc = np.nan_to_num(_col(sen, "direccion", 0).astype(float)).astype(int)
    stops = _col(sen, "stop", np.nan).astype(float)
    riesgos = _col(sen, "riesgo", np.nan).astype(float)
    objs = _col(sen, "objetivo", np.nan).astype(float)
    trailings = _col(sen, "trailing", np.nan).astype(float)
    salida_comun = _col(sen, "salida", False).astype(bool)
    salida_por_lado = {
        1: _col(sen, "salida_largo", False).astype(bool) if "salida_largo" in sen else salida_comun,
        -1: _col(sen, "salida_corto", False).astype(bool) if "salida_corto" in sen else salida_comun,
    }
    fund = _Funding(funding)
    adverso_primero = modelo == "conservador"
    n = len(df)
    trades: list[Trade] = []

    i = 0
    while i < n - 1:
        d = direc[i]
        if d == 0 or not (math.isfinite(riesgos[i]) or math.isfinite(stops[i])):
            i += 1
            continue
        j = i + 1
        entrada = o[j] * (1 + d * cfg.deslizamiento_pct)
        stop = entrada - d * riesgos[i] if math.isfinite(riesgos[i]) else stops[i]
        riesgo = (entrada - stop) * d
        if riesgo <= 0:
            trades.append(_trade(d, t[i], t[j], None, entrada, stop, None, None, "STOP_INVALIDO", 0, 0, 0, 0))
            i += 1
            continue
        obj = objs[i] if math.isfinite(objs[i]) else None
        if obj is None and cfg.objetivo_r:
            obj = entrada + d * cfg.objetivo_r * riesgo
        tp1 = None
        if cfg.tp1_r:
            nivel = entrada + d * cfg.tp1_r * riesgo
            if cfg.tp1_cierre >= 1:
                obj = nivel if obj is None else (min(obj, nivel) if d > 0 else max(obj, nivel))
            else:
                tp1 = nivel
        fee_r = cfg.fee_pct_por_lado * 2 * entrada / riesgo

        def r_de(precio: float, entrada=entrada, d=d, riesgo=riesgo) -> float:
            return (precio - entrada) * d / riesgo

        salidas = salida_por_lado[d]
        stop_act = stop
        abierta = 1.0  # fracción todavía abierta
        r_parcial = 0.0  # R ya realizado por la parte cerrada en TP1
        tp1_hecho = False
        mejor = peor = entrada
        salida = motivo = None
        momento = 0  # ms del cierre, para el funding
        k = j
        while k < n:
            # Gap: la vela abre ya pasada de un nivel (no aplica a la vela de entrada).
            if k > j:
                if (o[k] - stop_act) * d <= 0:
                    salida, motivo = o[k], "SL"
                elif obj is not None and (o[k] - obj) * d >= 0:
                    salida, motivo = o[k], "TP"
                elif tp1 is not None and not tp1_hecho and (o[k] - tp1) * d >= 0:
                    r_parcial, abierta, tp1_hecho = cfg.tp1_cierre * r_de(o[k]), 1 - cfg.tp1_cierre, True
                if motivo:
                    peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
                    momento = t_ms[k]
                    break
            peor = min(peor, lo[k]) if d > 0 else max(peor, h[k])
            favorable, adverso = (h[k], lo[k]) if d > 0 else (lo[k], h[k])
            toca_stop = adverso * d <= stop_act * d
            toca_obj = obj is not None and favorable * d >= obj * d
            toca_tp1 = tp1 is not None and not tp1_hecho and favorable * d >= tp1 * d
            momento = t_ms[k] + paso // 2
            if toca_stop and (toca_obj or toca_tp1) and adverso_primero:
                salida, motivo = stop_act, "SL"
            elif toca_stop and not (toca_obj or toca_tp1):
                salida, motivo = stop_act, "SL"
            else:
                if toca_tp1:
                    r_parcial, abierta, tp1_hecho = cfg.tp1_cierre * r_de(tp1), 1 - cfg.tp1_cierre, True
                if toca_obj:
                    salida, motivo = obj, "TP"
                elif cfg.timeout_velas and k - j + 1 >= cfg.timeout_velas:
                    salida, motivo, momento = c[k], "TIMEOUT", t_ms[k] + paso
                elif salidas[k] and k + 1 < n:
                    k += 1
                    salida, motivo, momento = o[k], "SALIDA", t_ms[k]
                    peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
            if motivo:
                break
            # Gestión al cierre de la vela; rige desde la siguiente.
            mejor = max(mejor, h[k]) if d > 0 else min(mejor, lo[k])
            nuevo = stop_act
            if tp1_hecho or (cfg.breakeven_r and (mejor - entrada) * d >= cfg.breakeven_r * riesgo):
                nuevo = max(nuevo, entrada) if d > 0 else min(nuevo, entrada)
            if math.isfinite(trailings[k]) and trailings[k] > 0:
                candidato = mejor - d * trailings[k]
                nuevo = max(nuevo, candidato) if d > 0 else min(nuevo, candidato)
            stop_act = nuevo
            k += 1

        if motivo is None:
            if not cfg.cerrar_al_final:
                trades.append(
                    _trade(d, t[i], t[j], None, entrada, stop, obj, None, "SIN_RESOLVER", 0, fee_r, 0, n - j)
                )
                break
            k = n - 1
            salida, motivo, momento = c[k], "FIN", t_ms[k] + paso
        r_bruto = r_parcial + abierta * r_de(salida)
        if tp1_hecho:
            motivo = f"TP1+{motivo}"
        f_r = d * fund.entre(t_ms[j], momento) * entrada / riesgo
        mae_r = max(0.0, (entrada - peor) * d / riesgo)
        velas = k - j + 1
        trades.append(
            _trade(d, t[i], t[j], t[k], entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, velas, f_r)
        )
        if motivo.endswith("FIN"):
            break
        # La vela de salida puede generar una señal nueva (se ejecutaría en la siguiente).
        i = k
    return trades


def _trade(d, ts, ta, tc, entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, velas, f_r=0.0) -> Trade:
    resuelto = es_resuelto(motivo)
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
        r_neto=float(r_bruto - fee_r - f_r) if resuelto else 0.0,
        mae_r=float(mae_r),
        velas=int(velas),
        funding_r=float(f_r),
    )


def simular_ambos(
    df: pd.DataFrame, sen: pd.DataFrame, cfg: Config, funding: pd.Series | None = None
) -> dict[str, list[Trade]]:
    return {m: simular(df, sen, cfg, m, funding) for m in ("conservador", "optimista")}
