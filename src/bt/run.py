"""Corre una estrategia sobre una ventana y la registra en la bitácora.

    python -m bt.run donchian_breakout BTCUSDT 1d --desde 2021-01-01 --nota "prueba"
    python -m bt.run donchian_breakout BTCUSDT 1d -p entrada=55 -p salida=20

Por defecto la ventana termina en el corte del holdout; `--holdout` lo incluye a propósito.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bt import bitacora, data, metrics, strategies
from bt.engine import Config, Trade, simular_ambos
from bt.splits import _ts, resolver_ventana


@dataclass
class Resultado:
    fila: dict
    informe: dict
    trades: dict[str, list[Trade]]


def correr(
    estrategia: str, df: pd.DataFrame, *, simbolo: str, intervalo: str, mercado: str = "futures",
    desde=None, hasta=None, holdout: bool = False, cfg: Config | None = None, params: dict | None = None,
    nota: str | None = None, funding: pd.Series | None = None,
) -> Resultado:
    cfg = cfg or Config()
    params = params or {}
    desde = _ts(desde) if desde is not None else df.index[0]
    hasta = _ts(hasta) if hasta is not None else df.index[-1] + pd.Timedelta(1, "ns")
    v = resolver_ventana(desde, hasta, holdout)
    avisos = [v.aviso] if v.aviso else []

    # Velas posteriores a la ventana no existen para la corrida: una posición abierta al final queda
    # SIN_RESOLVER (o se cierra al último cierre si cfg.cerrar_al_final) en vez de resolverse con
    # datos de afuera. Las anteriores sí se usan para calentar indicadores. La ventana se define
    # por la vela de ENTRADA: se anulan las señales cuya entrada (vela siguiente) cae antes de `desde`.
    df_v = df[df.index < v.hasta]
    sen = strategies.cargar(estrategia)(df_v, **params)
    return _simular_senales(
        estrategia, df_v, sen, v, avisos, simbolo=simbolo, intervalo=intervalo, mercado=mercado,
        cfg=cfg, params=params, nota=nota, funding=funding,
    )


def _simular_senales(
    estrategia: str, df_v: pd.DataFrame, sen: pd.DataFrame, v, avisos: list[str], *, simbolo: str,
    intervalo: str, mercado: str, cfg: Config, params: dict, nota: str | None, funding: pd.Series | None,
) -> Resultado:
    """Del DataFrame de señales al resultado: lo comparten `correr` y `correr_corte`."""
    entra_en = pd.Series(df_v.index, index=df_v.index).shift(-1)
    sen.loc[(entra_en < v.desde).to_numpy(), "direccion"] = 0

    en_ventana = df_v.index[df_v.index >= v.desde]
    if len(en_ventana) == 0:
        raise ValueError(f"no hay velas entre {v.desde} y {v.hasta}")
    if en_ventana[0] - v.desde > pd.Timedelta(days=7):
        avisos.append(f"los datos empiezan el {en_ventana[0].date()}, después de la fecha pedida")

    if funding is not None and len(funding):
        funding = funding[funding.index <= v.hasta]  # el cierre forzado ocurre justo en v.hasta
    modelos = simular_ambos(df_v, sen, cfg, funding)
    inf = metrics.informe(modelos)
    f = bitacora.fila(
        strategy=estrategia, symbol=simbolo, interval=intervalo, mercado=mercado,
        desde=en_ventana[0].isoformat(), hasta=en_ventana[-1].isoformat(), tramo=v.tramo,
        config={**cfg.como_dict(), "params": params, "funding": funding is not None and len(funding) > 0},
        informe=inf, avisos=avisos, nota=nota,
    )
    return Resultado(f, inf, modelos)


def alinear(velas: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Las velas de todos los símbolos sobre el mismo índice (la unión de fechas); NaN donde un
    símbolo no tiene vela. Así la estrategia de corte transversal compara en cada fecha."""
    idx = sorted(set().union(*(df.index for df in velas.values())))
    idx = pd.DatetimeIndex(idx, name="time")
    return {s: df.reindex(idx) for s, df in velas.items()}


def correr_corte(
    estrategia: str, velas: dict[str, pd.DataFrame], *, miembros: dict[str, list[str]] | None = None,
    intervalo: str, mercado: str = "futures", desde=None, hasta=None, holdout: bool = False,
    cfg: Config | None = None, params: dict | None = None, nota: str | None = None,
    funding: dict[str, pd.Series] | None = None,
) -> dict[str, Resultado]:
    """Estrategia de corte transversal: `senales_corte(velas, miembros, **params)` ve todos los
    símbolos alineados por fecha y devuelve un DataFrame de señales por símbolo. Desde ahí cada
    símbolo se simula con el motor de siempre (R neto, comisión, stops, bitácora)."""
    cfg = cfg or Config()
    params = params or {}
    funding = funding or {}
    inicio = min(df.index[0] for df in velas.values())
    fin = max(df.index[-1] for df in velas.values())
    desde = _ts(desde) if desde is not None else inicio
    hasta = _ts(hasta) if hasta is not None else fin + pd.Timedelta(1, "ns")
    v = resolver_ventana(desde, hasta, holdout)

    # Sin velas posteriores a la ventana (igual que `correr`); el ranking de `t` sólo ve hasta `t`.
    recortadas = {s: df[df.index < v.hasta] for s, df in velas.items()}
    recortadas = {s: df for s, df in recortadas.items() if len(df)}
    alineadas = alinear(recortadas)
    sen_todas = strategies.cargar_corte(estrategia)(alineadas, miembros, **params)

    out: dict[str, Resultado] = {}
    for s, df_v in recortadas.items():
        if s not in sen_todas:
            raise KeyError(f"la estrategia de corte `{estrategia}` no devolvió señales para {s}")
        sen = sen_todas[s].reindex(df_v.index)
        sen["direccion"] = sen["direccion"].fillna(0).astype(int)
        try:
            out[s] = _simular_senales(
                estrategia, df_v, sen, v, [v.aviso] if v.aviso else [], simbolo=s, intervalo=intervalo,
                mercado=mercado, cfg=cfg, params=params, nota=nota, funding=funding.get(s),
            )
        except ValueError:
            continue  # sin velas en la ventana (p. ej. un retirado): no tumba a los demás
    if not out:
        raise ValueError(f"no hay velas entre {v.desde} y {v.hasta}")
    return out


def _valor(s: str):
    for conv in (int, float):
        try:
            return conv(s)
        except ValueError:
            pass
    return {"true": True, "false": False}.get(s.lower(), s)


def resumen(r: Resultado) -> str:
    f, g = r.fila, r.informe["global"]
    ic = f"[{g['ic95'][0]:+.3f}, {g['ic95'][1]:+.3f}]" if g["ic95"] else "[—]"
    lineas = [
        f"{f['strategy']} {f['symbol']} {f['interval']}  {f['desde'][:10]}→{f['hasta'][:10]}  {f['tramo']}",
        f"  n={g['n']}  avgRNeto={g['avgRNeto']:+.3f} {ic}  bruto={g['avgR']:+.3f}  "
        f"acierto={g['winRatePct']:.0f}%  brecha modelos={r.informe['brechaEntreModelosR']:+.3f}",
        "  tramos: "
        + "  ".join(f"{t['desde']}:{t['avgRNeto']:+.2f}(n={t['n']})" for t in r.informe["porTramo"]),
        f"  concluyente: {'sí' if r.informe['concluyente'] else 'no'}",
    ]
    lineas += [f"    - {x}" for x in r.informe["porQueNoConcluyente"]]
    lineas += [f"  ⚠ {x}" for x in f["avisos"]]
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("estrategia")
    p.add_argument("simbolo")
    p.add_argument("intervalo")
    p.add_argument("--mercado", default="futures", choices=sorted(data.BASES))
    p.add_argument("--desde")
    p.add_argument("--hasta")
    p.add_argument("--holdout", action="store_true", help="incluir el holdout (se mira UNA vez)")
    p.add_argument("-p", "--param", action="append", default=[], help="k=v para la estrategia")
    p.add_argument("--fee", type=float, default=Config.fee_pct_por_lado, help="comisión por lado")
    p.add_argument("--deslizamiento", type=float, default=0.0, help="fracción del precio, en contra")
    p.add_argument("--timeout", type=int, default=None, help="velas")
    p.add_argument("--objetivo-r", type=float, default=None)
    p.add_argument("--cerrar-al-final", action="store_true", help="cerrar lo abierto al último cierre")
    p.add_argument("--funding", action="store_true", help="cobrar funding (data/funding/<SIMBOLO>.csv)")
    p.add_argument("--nota")
    p.add_argument("--datos", type=Path, default=data.DIR_DATOS)
    p.add_argument("--no-registrar", action="store_true")
    p.add_argument("--json", action="store_true", help="imprimir la fila de la bitácora")
    a = p.parse_args(argv)

    params = dict(kv.split("=", 1) for kv in a.param)
    params = {k: _valor(v) for k, v in params.items()}
    cfg = Config(a.fee, a.deslizamiento, a.timeout, a.objetivo_r, a.cerrar_al_final)
    df = data.cargar(a.simbolo, a.intervalo, a.mercado, a.datos)
    r = correr(
        a.estrategia, df, simbolo=a.simbolo.upper(), intervalo=a.intervalo, mercado=a.mercado,
        desde=a.desde, hasta=a.hasta, holdout=a.holdout, cfg=cfg, params=params, nota=a.nota,
        funding=data.cargar_funding(a.simbolo) if a.funding else None,
    )
    print(json.dumps(r.fila, ensure_ascii=False, indent=2) if a.json else resumen(r))
    if not a.no_registrar:
        bitacora.registrar(r.fila)


if __name__ == "__main__":
    main()
