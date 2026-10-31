"""Fase 2: el motor tiene que reproducir resultados ya medidos en btc-signal-web.

Si no los reproduce, ningún número nuevo de este repo es confiable. Cada caso agrupa las
operaciones de todos sus símbolos (como la "cartera" de los scripts originales) y compara n y
avgR neto contra lo registrado en `btc-signal-web/DECISIONES.md`.

    python -m bt.validacion            # corre todos los casos con lo que haya en data/
    python -m bt.validacion --bajar    # baja antes velas y funding (necesita red)

Sale con código 1 si algún caso no reproduce.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

from bt import bitacora, data, metrics, run
from bt.engine import Config

TOKENS_14 = "ADA AVAX BNB BTC DOGE DOT ETH LINK LTC NEAR SOL TRX UNI XRP".split()
# Costo por lado de los scripts de tendencia: comisión 0.05% + deslizamiento 0.05%, y cierre forzado
# al final del tramo.
CFG_TENDENCIA = Config(fee_pct_por_lado=0.001, cerrar_al_final=True)
FIN_HOLDOUT_TENDENCIA = "2026-10-19"


@dataclass(frozen=True)
class Caso:
    nombre: str
    estrategia: str
    simbolos: list[str]
    intervalo: str
    mercado: str
    funding: bool
    esperado_n: int
    esperado_avg: float
    fuente: str
    cfg: Config = CFG_TENDENCIA
    holdout: bool = False
    desde: str | None = None
    hasta: str | None = None
    params: dict = field(default_factory=dict)
    # Tolerancias: los datos de data.binance.vision pueden diferir en alguna vela de los archivos
    # que usó btc-signal-web; una diferencia mayor que esto es un problema del motor o de los datos.
    tol_n: float = 0.02
    tol_avg: float = 0.02


CASOS = [
    Caso(
        "TREND_1D 14 tokens · desarrollo", "tendencia_donchian", [f"{s}USDT" for s in TOKENS_14],
        "1d", "futures", True, 567, 0.545, "DECISIONES.md, aprobada el 2026-10-20",
    ),
    Caso(
        "TREND_1D 14 tokens · holdout", "tendencia_donchian", [f"{s}USDT" for s in TOKENS_14],
        "1d", "futures", True, 107, 0.256, "DECISIONES.md, aprobada el 2026-10-20",
        holdout=True, desde="2025-09-09", hasta=FIN_HOLDOUT_TENDENCIA,
    ),
    Caso(
        "TREND_1D oro (PAXG spot) · desarrollo", "tendencia_donchian", ["PAXGUSDT"],
        "1d", "spot", False, 37, 0.022, "DECISIONES.md, rechazada el 2026-10-24",
    ),
]


@dataclass
class Resultado:
    caso: Caso
    n: int
    avg: float
    ic95: tuple[float, float] | None
    faltan: list[str]

    @property
    def reproduce(self) -> bool:
        c = self.caso
        if self.faltan:
            return False
        ok_n = abs(self.n - c.esperado_n) <= max(1, round(c.tol_n * c.esperado_n))
        return ok_n and abs(self.avg - c.esperado_avg) <= c.tol_avg


def correr_caso(c: Caso) -> Resultado:
    trades, faltan = [], []
    for s in c.simbolos:
        try:
            df = data.cargar(s, c.intervalo, c.mercado)
        except FileNotFoundError:
            faltan.append(s)
            continue
        fund = data.cargar_funding(s) if c.funding else None
        if c.funding and (fund is None or len(fund) == 0):
            faltan.append(f"{s} (funding)")
            continue
        r = run.correr(
            c.estrategia, df, simbolo=s, intervalo=c.intervalo, mercado=c.mercado, desde=c.desde,
            hasta=c.hasta, holdout=c.holdout, cfg=c.cfg, params=c.params, funding=fund,
            nota=f"validacion: {c.nombre}",
        )
        bitacora.registrar(r.fila)
        trades += r.trades["conservador"]
    g = metrics.calcular(trades)
    return Resultado(c, g["n"], g["avgRNeto"], g["ic95"], faltan)


def bajar(casos: list[Caso]) -> None:
    hechos = set()
    for c in casos:
        for s in c.simbolos:
            if (s, c.intervalo, c.mercado) not in hechos:
                print(f"bajando {c.mercado} {s} {c.intervalo}", flush=True)
                data.descargar(s, c.intervalo, "2020-01", c.mercado)
                hechos.add((s, c.intervalo, c.mercado))
            if c.funding and (s, "funding") not in hechos:
                data.descargar_funding(s, "2020-01")
                hechos.add((s, "funding"))


def informe(resultados: list[Resultado]) -> str:
    filas = [
        "| Caso | n esperado | n obtenido | avgR esperado | avgR obtenido | ±2 EE | Reproduce |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        ic = f"[{r.ic95[0]:+.3f}, {r.ic95[1]:+.3f}]" if r.ic95 else "—"
        estado = "✅" if r.reproduce else ("⚠️ faltan datos: " + ", ".join(r.faltan) if r.faltan else "❌")
        filas.append(
            f"| {r.caso.nombre} | {r.caso.esperado_n} | {r.n} | {r.caso.esperado_avg:+.3f} | "
            f"{r.avg:+.3f} | {ic} | {estado} |"
        )
    return "\n".join(filas)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bajar", action="store_true")
    p.add_argument("--caso", help="sólo los casos cuyo nombre contenga este texto")
    a = p.parse_args(argv)
    casos = [c for c in CASOS if not a.caso or a.caso.lower() in c.nombre.lower()]
    if a.bajar:
        bajar(casos)
    resultados = [correr_caso(c) for c in casos]
    print(informe(resultados))
    return 0 if all(r.reproduce for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
