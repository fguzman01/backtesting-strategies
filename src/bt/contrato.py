"""Contrato de `results/approved.json` con btc-signal-web (Fase 5).

btc-signal-web guarda una copia de este archivo (`src/config/factoryApproved.json`, actualizada por
PR) y la lee con tipos fijos en `src/config/factory.ts`. Si el formato cambia acá sin cambiar allá,
el bot deja de entender lo aprobado: por eso se valida en el CI.

    python -m bt.contrato            # valida results/approved.json; sale con 1 si no cumple
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RUTA = Path("results") / "approved.json"
CAMPOS = {
    "id": str, "estrategia": str, "params": dict, "mercado": str, "intervalo": str, "simbolos": list,
    "config": dict, "desarrollo": dict, "holdout": dict, "aprobada_en": str, "commit": str, "reporte": str,
    # Desde 2026-11-02 (retroalimentación de btc-signal-web): la ficha dice cuánto confiar.
    "nivel": str, "n_pruebas": int, "holdout_contaminado": bool,
}
NIVELES = {"aprobada", "observacion"}  # observacion = sólo paper, para observar
METRICAS = {"n": int, "avgRNeto": (int, float), "ic95": (list, type(None))}


def validar(datos: dict) -> list[str]:
    errores = []
    if not isinstance(datos, dict) or not isinstance(datos.get("estrategias"), list):
        return ["falta la lista `estrategias`"]
    ids = set()
    for i, e in enumerate(datos["estrategias"]):
        donde = f"estrategias[{i}]"
        if not isinstance(e, dict):
            errores.append(f"{donde}: no es un objeto")
            continue
        for campo, tipo in CAMPOS.items():
            if not isinstance(e.get(campo), tipo):
                errores.append(f"{donde}.{campo}: falta o no es {tipo.__name__}")
        if isinstance(e.get("nivel"), str) and e["nivel"] not in NIVELES:
            errores.append(f"{donde}.nivel: `{e['nivel']}` no es uno de {sorted(NIVELES)}")
        cupo = e.get("max_por_direccion")
        if cupo is not None and not (isinstance(cupo, int) and cupo >= 1):
            errores.append(f"{donde}.max_por_direccion: tiene que ser un entero ≥ 1 o null")
        if e.get("id") in ids:
            errores.append(f"{donde}.id: repetido ({e.get('id')})")
        ids.add(e.get("id"))
        for tramo in ("desarrollo", "holdout"):
            m = e.get(tramo) if isinstance(e.get(tramo), dict) else {}
            for campo, tipo in METRICAS.items():
                if not isinstance(m.get(campo), tipo):
                    errores.append(f"{donde}.{tramo}.{campo}: falta o tiene otro tipo")
            if isinstance(m.get("ic95"), list) and len(m["ic95"]) != 2:
                errores.append(f"{donde}.{tramo}.ic95: tiene que tener 2 valores")
        if isinstance(e.get("simbolos"), list) and not all(isinstance(s, str) for s in e["simbolos"]):
            errores.append(f"{donde}.simbolos: tienen que ser textos")
        if isinstance(e.get("config"), dict) and not isinstance(e["config"].get("timeout_velas"), int):
            errores.append(f"{donde}.config.timeout_velas: falta (el bot lo necesita para el tope)")
    return errores


def main(argv: list[str] | None = None) -> int:
    ruta = Path(argv[0]) if argv else RUTA
    if not ruta.exists():
        print(f"{ruta}: no existe (todavía no hay aprobadas): nada que validar")
        return 0
    errores = validar(json.loads(ruta.read_text(encoding="utf-8")))
    for e in errores:
        print(f"❌ {e}")
    if not errores:
        print(f"✅ {ruta}: cumple el contrato con btc-signal-web")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
