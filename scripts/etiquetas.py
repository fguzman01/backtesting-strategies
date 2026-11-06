"""Crea o actualiza en GitHub las etiquetas de `.operador.yml` (`grupo:nombre`). Idempotente.

    GH_TOKEN=... python scripts/etiquetas.py owner/repo        # usa la CLI `gh`
    python scripts/etiquetas.py --listar                       # sólo imprime lo que crearía
"""

import subprocess
import sys
from pathlib import Path

import yaml


def etiquetas(ruta: Path = Path(".operador.yml")) -> list[tuple[str, str, str]]:
    cfg = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return [(f"{grupo}:{nombre}", d["color"], d["descripcion"])
            for grupo, items in cfg["etiquetas"].items() for nombre, d in items.items()]


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "--listar":
        for nombre, color, desc in etiquetas():
            print(f"{nombre}\t#{color}\t{desc}")
        return 0
    repo = argv[0]
    for nombre, color, desc in etiquetas():
        subprocess.run(["gh", "label", "create", nombre, "--repo", repo, "--color", color, "--description", desc,
                        "--force"], check=True)
        print(f"ok {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
