"""Velas de Binance desde data.binance.vision.

Port de `btc-signal-web/scripts/bajar-klines-vision.py`: zips mensuales más los diarios del mes en
curso, porque la API REST tarda horas para años de velas finas y los zips minutos.

Uso:
    python -m bt.data BTCUSDT 1d 2020-01
    python -m bt.data PAXGUSDT 1d 2020-01 --mercado spot
    python -m bt.data BTCUSDT 1d 2020-01 --funding      # también data/funding/BTCUSDT.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

BASES = {
    "futures": "https://data.binance.vision/data/futures/um",
    "spot": "https://data.binance.vision/data/spot",
}
COLUMNAS = ["time", "open", "high", "low", "close", "volume"]
DIR_DATOS = Path("data") / "klines"
DIR_FUNDING = Path("data") / "funding"


def ruta_local(simbolo: str, intervalo: str, mercado: str = "futures", base: Path = DIR_DATOS) -> Path:
    return base / f"{mercado}-{simbolo.upper()}-{intervalo}.csv"


def _get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except Exception:
        return None


def _a_ms(t: int) -> int:
    # Desde 2025 los zips de spot vienen en microsegundos.
    return t // 1000 if t > 10**14 else t


def parsear_zip(blob: bytes) -> dict[int, list[str]]:
    """Filas `time -> [time, o, h, l, c, v]` de un zip de klines. Ignora cabeceras."""
    filas: dict[int, list[str]] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for nombre in z.namelist():
            texto = z.read(nombre).decode()
            for fila in csv.reader(io.StringIO(texto)):
                if not fila or not fila[0].strip().isdigit():
                    continue
                t = _a_ms(int(fila[0]))
                filas[t] = [str(t), *fila[1:6]]
    return filas


def _meses(desde: dt.date, hasta: dt.date):
    y, m = desde.year, desde.month
    while (y, m) <= (hasta.year, hasta.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


HILOS = 8


def _desde_incremental(destino: Path, inicio: dt.date) -> tuple[dt.date, dict[int, list[str]]]:
    """Si ya hay un CSV local, se conservan sus filas y se rebaja sólo desde el mes anterior a la última.

    Rebajar el último mes (y el anterior) cubre el caso de un mes que la vez pasada vino por diarios
    incompletos. Lo de antes no cambia: los zips mensuales de Binance son históricos fijos.
    """
    if not destino.exists():
        return inicio, {}
    with destino.open() as f:
        filas = {int(r[0]): r for r in csv.reader(f) if r and r[0].isdigit()}
    if not filas:
        return inicio, {}
    primera = dt.datetime.fromtimestamp(min(filas) / 1000, dt.UTC).date()
    if primera > inicio.replace(day=1) + dt.timedelta(days=62):
        # El archivo empieza mucho después de lo pedido: puede que antes no se pidiera tan atrás.
        return inicio, filas
    ultima = dt.datetime.fromtimestamp(max(filas) / 1000, dt.UTC).date()
    y, m = _mes_anterior(ultima)
    return max(inicio, dt.date(y, m, 1)), filas


def _mes_klines(raiz: str, raiz_d: str, simbolo: str, intervalo: str, y: int, m: int, hoy: dt.date):
    blob = _get(f"{raiz}/{simbolo}-{intervalo}-{y}-{m:02d}.zip")
    if blob:
        return parsear_zip(blob)
    filas: dict[int, list[str]] = {}
    if (y, m) >= (hoy.year, hoy.month) or (y, m) == _mes_anterior(hoy):
        # El mensual del mes en curso (y a veces del anterior) aún no existe: ir por diarios.
        d = dt.date(y, m, 1)
        while d.month == m and d < hoy:
            b = _get(f"{raiz_d}/{simbolo}-{intervalo}-{d.isoformat()}.zip")
            if b:
                filas.update(parsear_zip(b))
            d += dt.timedelta(days=1)
    return filas


def descargar(
    simbolo: str, intervalo: str, desde: str = "2020-01", mercado: str = "futures", base: Path = DIR_DATOS
) -> Path:
    """Baja desde `desde` (AAAA-MM) hasta ayer, en paralelo por mes, y completa el CSV local.

    Si el CSV ya existe sólo se rebajan los últimos meses (ver `_desde_incremental`).
    """
    simbolo = simbolo.upper()
    raiz = f"{BASES[mercado]}/monthly/klines/{simbolo}/{intervalo}"
    raiz_d = f"{BASES[mercado]}/daily/klines/{simbolo}/{intervalo}"
    hoy = dt.datetime.now(dt.UTC).date()
    destino = ruta_local(simbolo, intervalo, mercado, base)
    inicio, filas = _desde_incremental(destino, dt.datetime.strptime(desde, "%Y-%m").date())

    with ThreadPoolExecutor(HILOS) as ex:
        for parte in ex.map(lambda ym: _mes_klines(raiz, raiz_d, simbolo, intervalo, *ym, hoy),
                            list(_meses(inicio, hoy))):
            filas.update(parte)

    if not filas:
        raise RuntimeError(f"sin datos para {mercado} {simbolo} {intervalo} desde {desde}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        for t in sorted(filas):
            w.writerow(filas[t])
    return destino


def _mes_anterior(d: dt.date) -> tuple[int, int]:
    return (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)


def descargar_funding(simbolo: str, desde: str = "2020-01", base: Path = DIR_FUNDING) -> Path:
    """Funding histórico de futuros USDⓈ-M → data/funding/<SIMBOLO>.csv (time,rate)."""
    simbolo = simbolo.upper()
    raiz = f"{BASES['futures']}/monthly/fundingRate/{simbolo}"
    hoy = dt.datetime.now(dt.UTC).date()
    destino = base / f"{simbolo}.csv"
    inicio, previas = _desde_incremental(destino, dt.datetime.strptime(desde, "%Y-%m").date())
    filas: dict[int, str] = {t: r[1] for t, r in previas.items()}

    def mes(ym):
        blob = _get(f"{raiz}/{simbolo}-fundingRate-{ym[0]}-{ym[1]:02d}.zip")
        if not blob:
            return {}
        out = {}
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for fila in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())):
                if fila and fila[0].strip().isdigit():
                    # Un pago por minuto: distintas fuentes traen el mismo instante con ms de diferencia.
                    out.setdefault(int(fila[0]) // 60_000 * 60_000, fila[2])
        return out

    with ThreadPoolExecutor(HILOS) as ex:
        for parte in ex.map(mes, list(_meses(inicio, hoy))):
            filas.update(parte)
    if not filas:
        raise RuntimeError(f"sin funding para {simbolo} desde {desde}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "rate"])
        for t in sorted(filas):
            w.writerow([t, filas[t]])
    return destino


def cargar_funding(simbolo: str, base: Path = DIR_FUNDING) -> pd.Series:
    """Serie de tasas indexada por instante de pago (UTC). Vacía si no hay archivo."""
    ruta = base / f"{simbolo.upper()}.csv"
    if not ruta.exists():
        return pd.Series(dtype=float)
    df = pd.read_csv(ruta)
    indice = pd.to_datetime(df["time"], unit="ms", utc=True)
    return pd.Series(df["rate"].astype(float).to_numpy(), index=indice)


def cargar(simbolo: str, intervalo: str, mercado: str = "futures", base: Path = DIR_DATOS) -> pd.DataFrame:
    """DataFrame indexado por la apertura de la vela (UTC), columnas open/high/low/close/volume."""
    ruta = ruta_local(simbolo, intervalo, mercado, base)
    if not ruta.exists():
        raise FileNotFoundError(f"{ruta} no existe. Bajalo con: python -m bt.data {simbolo} {intervalo}")
    return desde_csv(ruta)


def desde_csv(ruta: Path | str) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    df.index = pd.to_datetime(df.pop("time"), unit="ms", utc=True)
    df.index.name = "time"
    return df.astype(float).sort_index()


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("simbolo")
    p.add_argument("intervalo")
    p.add_argument("desde", nargs="?", default="2020-01", help="AAAA-MM")
    p.add_argument("--mercado", choices=sorted(BASES), default="futures")
    p.add_argument("--funding", action="store_true", help="bajar también el funding (sólo futuros)")
    a = p.parse_args(argv)
    if a.funding:
        print(descargar_funding(a.simbolo, a.desde))
    ruta = descargar(a.simbolo, a.intervalo, a.desde, a.mercado)
    df = desde_csv(ruta)
    print(f"{ruta}: {len(df)} velas, {df.index[0]} → {df.index[-1]}")


if __name__ == "__main__":
    main()
