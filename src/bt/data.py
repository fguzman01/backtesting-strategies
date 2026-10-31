"""Velas de Binance desde data.binance.vision.

Port de `btc-signal-web/scripts/bajar-klines-vision.py`: zips mensuales más los diarios del mes en
curso, porque la API REST tarda horas para años de velas finas y los zips minutos.

Uso:
    python -m bt.data BTCUSDT 1d 2020-01
    python -m bt.data PAXGUSDT 1d 2020-01 --mercado spot
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

BASES = {
    "futures": "https://data.binance.vision/data/futures/um",
    "spot": "https://data.binance.vision/data/spot",
}
COLUMNAS = ["time", "open", "high", "low", "close", "volume"]
DIR_DATOS = Path("data") / "klines"


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


def descargar(
    simbolo: str, intervalo: str, desde: str = "2020-01", mercado: str = "futures", base: Path = DIR_DATOS
) -> Path:
    """Baja todo desde `desde` (AAAA-MM) hasta ayer y sobrescribe el CSV local."""
    simbolo = simbolo.upper()
    raiz = f"{BASES[mercado]}/monthly/klines/{simbolo}/{intervalo}"
    raiz_d = f"{BASES[mercado]}/daily/klines/{simbolo}/{intervalo}"
    hoy = dt.datetime.now(dt.UTC).date()
    inicio = dt.datetime.strptime(desde, "%Y-%m").date()
    filas: dict[int, list[str]] = {}

    for y, m in _meses(inicio, hoy):
        blob = _get(f"{raiz}/{simbolo}-{intervalo}-{y}-{m:02d}.zip")
        if blob:
            filas.update(parsear_zip(blob))
        elif (y, m) >= (hoy.year, hoy.month) or (y, m) == _mes_anterior(hoy):
            # El mensual del mes en curso (y a veces del anterior) aún no existe: ir por diarios.
            d = dt.date(y, m, 1)
            while d.month == m and d < hoy:
                b = _get(f"{raiz_d}/{simbolo}-{intervalo}-{d.isoformat()}.zip")
                if b:
                    filas.update(parsear_zip(b))
                d += dt.timedelta(days=1)

    if not filas:
        raise RuntimeError(f"sin datos para {mercado} {simbolo} {intervalo} desde {desde}")
    destino = ruta_local(simbolo, intervalo, mercado, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        for t in sorted(filas):
            w.writerow(filas[t])
    return destino


def _mes_anterior(d: dt.date) -> tuple[int, int]:
    return (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)


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
    a = p.parse_args(argv)
    ruta = descargar(a.simbolo, a.intervalo, a.desde, a.mercado)
    df = desde_csv(ruta)
    print(f"{ruta}: {len(df)} velas, {df.index[0]} → {df.index[-1]}")


if __name__ == "__main__":
    main()
