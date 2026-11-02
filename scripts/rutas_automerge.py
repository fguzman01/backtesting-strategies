"""¿Puede fusionarse solo este PR de la rutina? Lee `<estado> <ruta>` por línea en stdin.

Permitido: specs, estrategias y tests NUEVOS, y cambios a 02-DOCS/ideas.md y 02-DOCS/catalogo.md
(el explorador). Cualquier otra cosa
(results/, approved.json, el motor, workflows, el Brain, specs o estrategias existentes) exige que
Felipe lo revise. Sale con 0 si se puede fusionar, 1 si no (e imprime por qué).
"""

import re
import sys

NUEVOS = [r"specs/\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.yaml", r"src/bt/strategies/[a-z0-9_]+\.py",
          r"tests/test_estrategia_[a-z0-9_]+\.py"]
EDITABLES = [r"02-DOCS/ideas\.md", r"02-DOCS/catalogo\.md"]


def motivo(estado: str, ruta: str) -> str | None:
    if any(re.fullmatch(p, ruta) for p in EDITABLES) and estado in ("added", "modified"):
        return None
    if any(re.fullmatch(p, ruta) for p in NUEVOS):
        return None if estado == "added" else f"{ruta}: sólo se permite agregar, no {estado}"
    return f"{ruta}: fuera de las rutas que la rutina puede fusionar sola"


def main() -> int:
    lineas = [x.split(None, 1) for x in sys.stdin.read().splitlines() if x.strip()]
    if not lineas:
        print("el PR no cambia archivos")
        return 1
    problemas = [m for e, r in lineas if (m := motivo(e, r.strip()))]
    for p in problemas:
        print(p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
