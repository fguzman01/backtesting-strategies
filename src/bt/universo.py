"""Universo sin sesgo de supervivencia: los futuros USDT más operados de CADA mes, incluidos los que
después Binance retiró.

Medir sólo en los tokens que siguen vivos hoy infla cualquier estrategia que compre: los que
murieron (LUNA, FTT, SRM...) no aparecen. data.binance.vision conserva su historia, así que se puede
reconstruir el universo como era en cada fecha.

Regla (fija, sin mirar resultados): para el mes M, los `TOP_MAX` perpetuos USDT con más volumen en
dólares en el mes M-1, entre los que tienen al menos `MESES_MINIMOS` meses completos de historia
(para que los indicadores estén calientes) y no son monedas estables. Sólo usa datos anteriores a M:
no hay look-ahead. Una spec elige `top` ≤ `TOP_MAX`.

    python -m bt.universo --construir     # baja volúmenes mensuales (incremental) y escribe la tabla

La tabla se versiona en `results/universo/futures-usdt.json`: misma tabla, mismo universo
(determinismo). La actualiza cada mes el workflow `adelante`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import sys
import time
import urllib.parse
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bt.data import _get

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DESCARGA = S3  # el mismo contenido que data.binance.vision; responde también donde ese dominio no llega
PREFIJO = "data/futures/um/monthly/klines/"
DIR_VOL = Path("data") / "universo" / "volumen"
TABLA = Path("results") / "universo" / "futures-usdt.json"
TOP_MAX = 50
MESES_MINIMOS = 3
PRIMER_MES = "2019-12"  # los perpetuos USDT empiezan en sep-2019
# Monedas estables y pares que no son un activo con riesgo propio.
ESTABLES = {"USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "EUR", "GBP", "AEUR", "USDE", "PYUSD", "UST", "USTC"}


def es_candidato(simbolo: str) -> bool:
    if not simbolo.endswith("USDT") or "_" in simbolo:  # los trimestrales llevan fecha: BTCUSDT_230331
        return False
    base = simbolo[: -len("USDT")]
    return bool(base) and base not in ESTABLES


def _listar(prefijo: str) -> tuple[list[str], list[str]]:
    """(subcarpetas, archivos) de un prefijo del bucket, con paginación."""
    carpetas, archivos, marca = [], [], ""
    while True:
        url = f"{S3}?prefix={urllib.parse.quote(prefijo)}&delimiter=/&marker={urllib.parse.quote(marca)}"
        blob = None
        for intento in range(4):  # el bucket a veces corta con muchas peticiones en paralelo
            blob = _get(url)
            if blob is not None:
                break
            time.sleep(2 ** intento)
        if blob is None:
            raise RuntimeError(f"no se pudo listar {prefijo}")
        texto = blob.decode()
        carpetas += re.findall(r"<Prefix>([^<]+/)</Prefix>", texto)[1 if prefijo else 0:]
        archivos += re.findall(r"<Key>([^<]+)</Key>", texto)
        if "<IsTruncated>true</IsTruncated>" not in texto:
            return [c for c in carpetas if c != prefijo], archivos
        marca = (re.findall(r"<NextMarker>([^<]+)</NextMarker>", texto) or [(carpetas or archivos)[-1]])[-1]


def listar_simbolos() -> list[str]:
    carpetas, _ = _listar(PREFIJO)
    return sorted(c[len(PREFIJO):].strip("/") for c in carpetas if es_candidato(c[len(PREFIJO):].strip("/")))


def _volumen_zip(blob: bytes) -> float | None:
    """Suma del volumen en la moneda cotizada (USDT, columna 7) de las velas diarias del mes."""
    total, filas = 0.0, 0
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for nombre in z.namelist():
            for linea in z.read(nombre).decode().splitlines():
                campos = linea.split(",")
                if campos and campos[0].strip().isdigit() and len(campos) > 7:
                    total += float(campos[7])
                    filas += 1
    return total if filas else None


def volumen_mensual(simbolo: str, hoy: dt.date | None = None, base: Path = DIR_VOL) -> dict[str, float]:
    """{AAAA-MM: volumen en USDT} de un símbolo, incremental: sólo baja los meses que faltan."""
    hoy = hoy or dt.date.today()
    ruta = base / f"{simbolo}.json"
    actual: dict[str, float] = json.loads(ruta.read_text()) if ruta.exists() else {}
    _, archivos = _listar(f"{PREFIJO}{simbolo}/1d/")  # las velas 1mo dejaron de publicarse en 2024
    mes_actual = f"{hoy.year:04d}-{hoy.month:02d}"
    for clave in archivos:
        m = re.search(r"-1d-(\d{4}-\d{2})\.zip$", clave)
        if not m or m.group(1) in actual or m.group(1) >= mes_actual:
            continue
        blob = _get(f"{DESCARGA}/{clave}") or _get(f"{DESCARGA}/{clave}")
        v = _volumen_zip(blob) if blob else None
        if v is not None:
            actual[m.group(1)] = v
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(dict(sorted(actual.items()))))
    return actual


def _mes(s: str, delta: int) -> str:
    y, m = int(s[:4]), int(s[5:7]) + delta
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def armar_tabla(volumenes: dict[str, dict[str, float]], hasta: str, top: int = TOP_MAX) -> dict[str, list[str]]:
    """{mes M: los `top` con más volumen en M-1 y al menos MESES_MINIMOS meses de historia}. Puro."""
    tabla, m = {}, PRIMER_MES
    while m <= hasta:
        previo = _mes(m, -1)
        historia = [_mes(m, -k) for k in range(1, MESES_MINIMOS + 1)]
        candidatos = [(v[previo], s) for s, v in volumenes.items() if all(h in v for h in historia)]
        candidatos.sort(key=lambda x: (-x[0], x[1]))
        if candidatos:
            tabla[m] = [s for _, s in candidatos[:top]]
        m = _mes(m, 1)
    return tabla


def construir(hoy: dt.date | None = None, hilos: int = 16) -> Path:
    hoy = hoy or dt.date.today()
    simbolos = listar_simbolos()
    with ThreadPoolExecutor(hilos) as ex:
        volumenes = dict(zip(simbolos, ex.map(lambda s: volumen_mensual(s, hoy), simbolos), strict=True))
    tabla = armar_tabla(volumenes, f"{hoy.year:04d}-{hoy.month:02d}")
    TABLA.parent.mkdir(parents=True, exist_ok=True)
    TABLA.write_text(json.dumps({
        "regla": f"top {TOP_MAX} perpetuos USDT por volumen en USDT del mes anterior; ≥ {MESES_MINIMOS} meses de "
                 "historia; sin monedas estables ni trimestrales. Incluye los retirados después.",
        "simbolosConsiderados": len(simbolos),
        "meses": tabla,
    }, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    return TABLA


def cargar_tabla(ruta: Path = TABLA) -> dict[str, list[str]]:
    if not ruta.exists():
        raise FileNotFoundError(f"{ruta}: falta la tabla del universo; correr `python -m bt.universo --construir`")
    return json.loads(ruta.read_text(encoding="utf-8"))["meses"]


def miembros(top: int, tabla: dict[str, list[str]], desde: str | None = None) -> dict[str, set[str]]:
    """{símbolo: meses en que estuvo entre los `top`} (desde el mes `desde`, AAAA-MM, si se da)."""
    out: dict[str, set[str]] = {}
    for mes, lista in tabla.items():
        if desde and mes < desde:
            continue
        for s in lista[:top]:
            out.setdefault(s, set()).add(mes)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--construir", action="store_true")
    a = p.parse_args(argv)
    if a.construir:
        ruta = construir()
        meses = cargar_tabla(ruta)
        ultimo = max(meses)
        print(f"{ruta}: {len(meses)} meses; {ultimo}: {', '.join(meses[ultimo][:10])}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
