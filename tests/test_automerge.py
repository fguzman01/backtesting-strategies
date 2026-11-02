import subprocess
import sys

import pytest

CASOS = [
    ("added specs/2026-11-02-algo-nuevo.yaml\nadded src/bt/strategies/rsi_dos.py\n"
     "added tests/test_estrategia_rsi_dos.py\nmodified 02-DOCS/ideas.md", 0),
    ("modified 02-DOCS/ideas.md", 0),
    ("modified 02-DOCS/catalogo.md\nmodified 02-DOCS/ideas.md", 0),  # PR del explorador
    ("modified 02-DOCS/alcance.md", 1),
    ("modified specs/2026-10-31-trend1d-tope-7d.yaml", 1),        # editar una spec existente
    ("modified src/bt/strategies/tendencia_donchian.py", 1),     # cambiar una estrategia existente
    ("added results/approved.json", 1),                           # lo que va a dinero real
    ("modified src/bt/engine.py", 1),
    ("modified .github/workflows/evaluar.yml", 1),
    ("modified 02-DOCS/decisiones.md", 1),
    ("added specs/PLANTILLA2.yaml", 1),
    ("", 1),
]


@pytest.mark.parametrize("entrada, esperado", CASOS)
def test_rutas_automerge(entrada, esperado):
    r = subprocess.run([sys.executable, "scripts/rutas_automerge.py"], input=entrada, text=True, capture_output=True)
    assert r.returncode == esperado, r.stdout
