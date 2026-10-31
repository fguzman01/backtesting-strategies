"""Registro de corridas: `results/mediciones.jsonl`.

Cada corrida deja una fila con el commit, la ventana EFECTIVA, el tramo y toda la config que cambia
la respuesta. Es un archivo del repo a propósito: el registro de qué se midió viaja versionado con
el código que lo midió. Esquema compatible con `btc-signal-web/data/mediciones.jsonl`.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

RUTA = Path("results") / "mediciones.jsonl"


def commit_actual() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        sucio = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True
        ).stdout.strip()
        return f"{sha}+cambios" if sucio else sha
    except Exception:
        return "sin-git"


def fila(
    *, strategy: str, symbol: str, interval: str, mercado: str, desde: str, hasta: str, tramo: str,
    config: dict, informe: dict, avisos: list[str], nota: str | None,
) -> dict:
    g = informe["global"]
    return {
        "ts": dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "commit": commit_actual(),
        "strategy": strategy,
        "symbol": symbol,
        "interval": interval,
        "mercado": mercado,
        "desde": desde,
        "hasta": hasta,
        "tramo": tramo,
        "config": config,
        "n": g["n"],
        "avgR": g["avgR"],
        "avgRNeto": g["avgRNeto"],
        "ic95": list(g["ic95"]) if g["ic95"] else None,
        "winRatePct": g["winRatePct"],
        "totalRNeto": g["totalRNeto"],
        "brechaEntreModelosR": informe["brechaEntreModelosR"],
        "concluyente": informe["concluyente"],
        "porQueNoConcluyente": informe["porQueNoConcluyente"],
        "porMotivo": g["porMotivo"],
        "avisos": avisos,
        "nota": nota,
    }


def registrar(entrada: dict, ruta: Path = RUTA) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a") as f:
        f.write(json.dumps(entrada, ensure_ascii=False, sort_keys=False) + "\n")


def leer(ruta: Path = RUTA) -> list[dict]:
    if not ruta.exists():
        return []
    return [json.loads(x) for x in ruta.read_text().splitlines() if x.strip()]
