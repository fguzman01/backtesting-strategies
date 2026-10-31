import pandas as pd
import pytest

from bt.engine import Trade
from bt.metrics import calcular, cuantos_tramos, informe, intervalo
from bt.splits import HOLDOUT_DESDE, clasificar, resolver_ventana


def tr(r, dia, motivo="TP"):
    return Trade(1, dia, dia, dia, 100, 95, None, None, motivo, r, 0.0, r, 0.0, 1)


def test_intervalo_varianza_muestral():
    lo, hi = intervalo([1.0, -1.0, 1.0, -1.0])
    # media 0, sd muestral 1.1547, ee 0.5774
    assert lo == pytest.approx(-1.1547, abs=1e-3) and hi == pytest.approx(1.1547, abs=1e-3)
    assert intervalo([1.0]) is None


def test_no_resueltos_no_cuentan():
    m = calcular([tr(1, "2024-01-01"), tr(0, "2024-01-02", "SIN_RESOLVER")])
    assert m["n"] == 1 and m["avgRNeto"] == 1


def test_cuantos_tramos():
    assert [cuantos_tramos(n) for n in (2, 6, 9, 12, 100)] == [2, 2, 3, 4, 4]


def test_concluyente_y_no_concluyente():
    dias = [f"2024-{m:02d}-01" for m in range(1, 13)]
    buenos = [tr(0.5, d) for d in dias]
    bueno = informe({"conservador": buenos, "optimista": buenos})
    assert bueno["concluyente"] and bueno["global"]["n"] == 12

    mixtos = [tr(1.0 if i < 6 else -0.8, d) for i, d in enumerate(dias)]
    malo = informe({"conservador": mixtos, "optimista": mixtos})
    assert not malo["concluyente"]
    assert any("signo" in x for x in malo["porQueNoConcluyente"])

    corto = informe({"conservador": buenos[:5], "optimista": buenos[:5]})
    assert any("muestra corta" in x for x in corto["porQueNoConcluyente"])


def test_brecha_entre_modelos_mayor_que_avgR():
    dias = [f"2024-{m:02d}-01" for m in range(1, 13)]
    cons = [tr(0.05, d) for d in dias]
    opt = [tr(0.5, d) for d in dias]
    inf = informe({"conservador": cons, "optimista": opt})
    assert any("modelos de llenado" in x for x in inf["porQueNoConcluyente"])


def test_holdout_fijo():
    assert HOLDOUT_DESDE == pd.Timestamp("2025-09-09", tz="UTC")
    assert clasificar("2024-01-01", "2025-01-01") == "desarrollo"
    assert clasificar("2025-10-01", "2026-01-01") == "holdout"
    assert clasificar("2025-01-01", "2026-01-01") == "mixto"


def test_por_defecto_recorta_en_el_holdout_y_avisa():
    v = resolver_ventana("2024-01-01", "2026-06-01")
    assert v.hasta == HOLDOUT_DESDE and v.tramo == "desarrollo" and "recortada" in v.aviso


def test_holdout_pedido_a_proposito():
    v = resolver_ventana("2025-09-09", "2026-06-01", holdout=True)
    assert v.tramo == "holdout" and "UNA vez" in v.aviso
    with pytest.raises(ValueError):
        resolver_ventana("2025-10-01", "2026-06-01")
