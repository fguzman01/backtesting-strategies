import copy
import json

import numpy as np
import pandas as pd
import pytest
import yaml

from bt import evaluar as ev_mod
from bt import sitio
from bt.engine import Config
from bt.nulo import control_nulo
from bt.run import correr
from bt.spec import SpecInvalida, cargar, desde_dict

BASE = {
    "id": "2026-11-01-prueba",
    "estado": "pre-registrada",
    "hipotesis": "La tendencia diaria persiste.",
    "horizonte": {"tipo": "diario"},
    "estrategia": {"modulo": "tendencia_donchian", "params": {"entrada": 20, "salida": 10}},
    "universo": {"mercado": "futures", "simbolos": ["AAAUSDT", "BBBUSDT"], "intervalo": "1d", "funding": True},
    "config": {"fee_pct_por_lado": 0.001, "timeout_velas": 7},
    "ventana_desarrollo": {"desde": "2020-01-01"},
    # Criterio laxo a propósito: estos tests ejercitan el flujo, no la exigencia (que se prueba aparte).
    "criterio_aprobacion": {"n_minimo": 10, "ic95_excluye_cero": False, "concluyente": False,
                            "supera_nulo_p95": False,
                            "holdout": {"avgRNeto_positivo": True, "sin_mejores_no_negativo": False}},
}


def con(**cambios):
    d = copy.deepcopy(BASE)
    for ruta, v in cambios.items():
        nodo = d
        *pre, ult = ruta.split("__")
        for k in pre:
            nodo = nodo[k]
        nodo[ult] = v
    return d


# ── Specs ────────────────────────────────────────────────────────────────────

def test_spec_valida():
    s = desde_dict(BASE)
    assert s.simbolos == ["AAAUSDT", "BBBUSDT"] and s.cfg.timeout_velas == 7 and s.cfg.cerrar_al_final
    assert s.criterio.n_minimo == 10 and s.funding


@pytest.mark.parametrize("cambio, mensaje", [
    ({"universo__intervalo": "1w"}, "fuera del alcance"),
    ({"config__timeout_velas": 15}, "14 como máximo"),
    ({"config__timeout_velas": None}, "timeout_velas"),
    ({"config__fee_pct_por_lado": 0}, "comisión"),
    ({"estado": "lista"}, "estado"),
    ({"horizonte__tipo": "posicional"}, "horizonte.tipo"),
    ({"estrategia__modulo": "../os"}, "módulo"),
    ({"universo__mercado": "spot"}, "funding sólo existe en futuros"),
    ({"criterio_aprobacion__inventado": 1}, "desconocidos"),
])
def test_spec_invalida(cambio, mensaje):
    with pytest.raises(SpecInvalida, match=mensaje):
        desde_dict(con(**cambio))


def test_timeout_en_horas_se_mide_en_dias():
    d = con(universo__intervalo="1h", config__timeout_velas=24 * 14, horizonte__tipo="swing")
    assert desde_dict(d).cfg.timeout_velas == 336
    with pytest.raises(SpecInvalida):
        desde_dict(con(universo__intervalo="1h", config__timeout_velas=24 * 14 + 1))


def test_id_debe_coincidir_con_el_archivo(tmp_path):
    ruta = tmp_path / "otro-nombre.yaml"
    ruta.write_text(yaml.safe_dump(BASE))
    with pytest.raises(SpecInvalida, match="no coincide"):
        cargar(ruta)


def test_plantilla_y_specs_del_repo_son_validas():
    from pathlib import Path
    for ruta in sorted(Path("specs").glob("*.yaml")):
        d = yaml.safe_load(ruta.read_text())
        desde_dict(d)  # la plantilla no tiene que coincidir en nombre
        if ruta.name != "PLANTILLA.yaml":
            cargar(ruta)


# ── Datos sintéticos ─────────────────────────────────────────────────────────

def mercado(semilla, deriva):
    rng = np.random.default_rng(semilla)
    idx = pd.date_range("2020-01-01", "2026-10-30", freq="1D", tz="UTC", name="time")
    close = 100 * np.exp(np.cumsum(rng.normal(deriva, 0.03, len(idx))))
    open_ = np.concatenate([[100.0], close[:-1]])
    r = np.abs(rng.normal(0, 0.015, len(idx))) * close
    df = pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + r,
                       "low": np.minimum(open_, close) - r, "close": close, "volume": 1.0}, index=idx)
    pagos = pd.date_range("2020-01-01", "2026-10-30", freq="8h", tz="UTC")
    return df, pd.Series(np.full(len(pagos), 0.0001), index=pagos)


@pytest.fixture
def mundo():
    datos = {"AAAUSDT": mercado(1, 0.003), "BBBUSDT": mercado(2, 0.003)}  # tendencia alcista fuerte
    return (lambda s, i, m: datos[s][0]), (lambda s: datos[s][1]), datos


def test_control_nulo_determinista_y_coherente(mundo):
    cv, cf, datos = mundo
    trades, d = {}, {}
    for s in datos:
        r = correr("tendencia_donchian", cv(s, "1d", "futures"), simbolo=s, intervalo="1d",
                   cfg=Config(0.001, timeout_velas=14), funding=cf(s))
        trades[s] = r.trades["conservador"]
        d[s] = (cv(s, "1d", "futures"), cf(s))
    desde, hasta = pd.Timestamp("2020-01-01", tz="UTC"), pd.Timestamp("2025-09-09", tz="UTC")
    a = control_nulo(trades, d, desde, hasta, Config(0.001), iteraciones=300)
    b = control_nulo(trades, d, desde, hasta, Config(0.001), iteraciones=300)
    assert a == b and a["iteraciones"] == 300
    assert a["p95"] > a["media"]
    # En un mercado que sube sin parar, entrar largo al azar también gana.
    assert a["media"] > 0


def test_evaluacion_aprobada_mira_el_holdout_y_escribe_todo(mundo, tmp_path):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(BASE), cv, cf, base=tmp_path)
    assert ev["veredicto"] == "APROBADA", ev["motivos"]
    assert ev["holdout"] is not None and ev["holdout"]["global"]["n"] > 0
    assert ev["holdout"]["ventana"][0] >= "2025-09-09"
    assert ev["desarrollo"]["ventana"][1] < "2025-09-09"
    assert any("alcance" in c["criterio"] for c in ev["criterios"])

    ev_mod.guardar(ev, tmp_path)
    aprobadas = json.loads((tmp_path / "approved.json").read_text())
    assert [e["id"] for e in aprobadas["estrategias"]] == ["2026-11-01-prueba"]
    assert aprobadas["estrategias"][0]["holdout"]["n"] == ev["holdout"]["global"]["n"]
    assert (tmp_path / "reports" / "2026-11-01-prueba.md").read_text().startswith("# 2026-11-01-prueba — APROBADA")
    guardada = json.loads((tmp_path / "evaluaciones" / "2026-11-01-prueba.json").read_text())
    assert "filas" not in guardada["desarrollo"]
    filas = (tmp_path / "mediciones.jsonl").read_text().splitlines()
    assert len(filas) == 8  # 2 símbolos × (desarrollo + holdout + 2 vecinos de estabilidad)
    assert ev_mod.evaluada("2026-11-01-prueba", tmp_path)


def test_si_falla_desarrollo_el_holdout_no_se_mira(mundo, tmp_path):
    cv, cf, _ = mundo
    d = con(criterio_aprobacion__supera_nulo_p95=True, criterio_aprobacion__n_minimo=10)
    d["criterio_aprobacion"]["tramos_positivos_minimo"] = 5  # imposible: hay como mucho 4 tramos
    ev = ev_mod.evaluar(desde_dict(d), cv, cf, base=tmp_path)
    assert ev["veredicto"] == "RECHAZADA" and ev["holdout"] is None
    assert any("tramos positivos" in m for m in ev["motivos"])
    ev_mod.guardar(ev, tmp_path)
    assert not (tmp_path / "approved.json").exists()
    assert "No se miró" in (tmp_path / "reports" / f"{d['id']}.md").read_text()


def test_muestra_chica_es_no_concluyente(mundo, tmp_path):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(con(criterio_aprobacion__n_minimo=100000)), cv, cf, base=tmp_path)
    assert ev["veredicto"] == "NO_CONCLUYENTE" and ev["holdout"] is None


def test_pendientes_y_no_reevaluar(tmp_path, monkeypatch, capsys):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / f"{BASE['id']}.yaml").write_text(yaml.safe_dump(BASE))
    borrador = con(id="2026-11-02-borrador", estado="borrador")
    (specs / "2026-11-02-borrador.yaml").write_text(yaml.safe_dump(borrador))
    res = tmp_path / "results"
    assert [s.id for s in ev_mod.pendientes(specs, res)] == [BASE["id"]]
    (res / "evaluaciones").mkdir(parents=True)
    (res / "evaluaciones" / f"{BASE['id']}.json").write_text("{}")
    assert ev_mod.pendientes(specs, res) == []

    monkeypatch.chdir(tmp_path)
    assert ev_mod.main([f"specs/{BASE['id']}.yaml"]) == 0
    assert "ya evaluada" in capsys.readouterr().out


def test_sitio_con_y_sin_evaluaciones(mundo, tmp_path):
    vacio = sitio.generar(tmp_path)
    assert "Todavía no hay evaluaciones" in vacio
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(BASE), cv, cf, base=tmp_path)
    ev["spec"]["hipotesis"] = "<script>alert(1)</script>"
    ev_mod.guardar(ev, tmp_path)
    pagina = sitio.generar(tmp_path)
    assert "2026-11-01-prueba" in pagina and "Aprobada" in pagina and "holdout →" in pagina
    assert "<script>alert(1)</script>" not in pagina  # el texto de la spec se escapa


def test_workflows_son_yaml_valido():
    from pathlib import Path
    for ruta in Path(".github/workflows").glob("*.yml"):
        yaml.safe_load(ruta.read_text())


def test_spec_con_gestion_de_posicion():
    d = con(config__tp1_r=1.0, config__tp1_cierre=0.5, config__breakeven_r=0.8)
    s = desde_dict(d)
    assert s.cfg.tp1_r == 1.0 and s.cfg.tp1_cierre == 0.5 and s.cfg.breakeven_r == 0.8
    with pytest.raises(SpecInvalida, match="tp1_cierre"):
        desde_dict(con(config__tp1_cierre=1.5))


def test_spec_historia_spot():
    assert desde_dict(con(universo__historia_spot=True)).historia_spot
    assert not desde_dict(BASE).historia_spot
    with pytest.raises(SpecInvalida, match="historia_spot"):
        desde_dict(con(universo__historia_spot=True, universo__mercado="spot", universo__funding=False))


def test_holdout_endurecido_habria_rechazado_a_trend4h():
    """Números reales de 2026-11-02-trend4h-tope-7d: con el criterio nuevo (por defecto) no pasa."""
    from bt.evaluar import _criterios_holdout
    d = copy.deepcopy(BASE)
    d["criterio_aprobacion"]["holdout"] = {"avgRNeto_positivo": True}  # el resto toma los defaults estrictos
    s = desde_dict(d)
    assert s.criterio.holdout_aguanta_costos and s.criterio.holdout_sin_mejores_no_negativo
    assert s.criterio.holdout_fraccion_desarrollo == pytest.approx(0.33)
    dev = {"global": {"avgRNeto": 0.245}}
    ho = {"global": {"n": 916, "avgRNeto": 0.036},
          "robustez": {"costosX": 1.5, "costos": {"avgRNeto": 0.004}, "sinMejores": 10, "sinTop": {"avgRNeto": -0.095}}}
    cr = {c["criterio"]: c["ok"] for c in _criterios_holdout(s, dev, ho)}
    assert cr["holdout: avgR neto > 0"]                         # el criterio viejo lo dejaba pasar
    assert cr["holdout: con costos ×1.5 avgR > 0"]              # +0.004: pasa por poco
    assert not cr["holdout: sin las 10 mejores avgR ≥ 0"]       # −0.095
    assert not cr["holdout: conserva ≥ 33% del avgR de desarrollo"]  # 0.036 < 0.081


def test_holdout_sano_pasa_el_criterio_estricto():
    from bt.evaluar import _criterios_holdout
    s = desde_dict(con(criterio_aprobacion__holdout={}))
    dev = {"global": {"avgRNeto": 0.20}}
    ho = {"global": {"n": 300, "avgRNeto": 0.12},
          "robustez": {"costosX": 1.5, "costos": {"avgRNeto": 0.09}, "sinMejores": 10, "sinTop": {"avgRNeto": 0.05}}}
    assert all(c["ok"] for c in _criterios_holdout(s, dev, ho))


# ── Retroalimentación de btc-signal-web (2026-11-02) ─────────────────────────

def test_holdout_contaminado_baja_a_observacion_y_entra_con_su_nivel(mundo, tmp_path):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(con(holdout_contaminado=True)), cv, cf, base=tmp_path)
    assert ev["veredicto"] == "OBSERVACION" and ev["nivel"] == "observacion" and ev["holdoutContaminado"]
    assert any("contaminado" in m for m in ev["motivos"])
    ev_mod.guardar(ev, tmp_path)
    e = json.loads((tmp_path / "approved.json").read_text())["estrategias"][0]
    assert e["nivel"] == "observacion" and e["holdout_contaminado"] and e["n_pruebas"] == 1
    from bt.contrato import validar
    assert validar({"estrategias": [e]}) == []


def test_antecedentes_cuentan_pruebas_y_contaminan_el_holdout(mundo, tmp_path):
    cv, cf, _ = mundo
    primera = ev_mod.evaluar(desde_dict(BASE), cv, cf, base=tmp_path)
    ev_mod.guardar(primera, tmp_path)
    ev = ev_mod.evaluar(desde_dict(con(id="2026-11-02-variante")), cv, cf, base=tmp_path)
    assert ev["nPruebas"] == 2 and [v["id"] for v in ev["variantes"]] == [BASE["id"]]
    assert ev["holdoutContaminado"] and ev["veredicto"] == "OBSERVACION"
    otra = ev_mod.evaluar(desde_dict(con(id="2026-11-02-otra", familia="otra")), cv, cf, base=tmp_path)
    assert otra["nPruebas"] == 1 and otra["veredicto"] == "APROBADA"
    d = con(id="2026-11-02-af", familia="otra", pruebas_previas=5)
    afuera = ev_mod.evaluar(desde_dict(d), cv, cf, base=tmp_path)
    assert afuera["nPruebas"] == 6


def test_comparacion_con_la_madre(mundo, tmp_path):
    cv, cf, _ = mundo
    d = con(madre={"nombre": "sin tope", "config": {"timeout_velas": 14}})
    ev = ev_mod.evaluar(desde_dict(d), cv, cf, base=tmp_path)
    c = ev["comparacionMadre"]["desarrollo"]
    assert c["madre"] == "sin tope" and c["nHija"] == ev["desarrollo"]["global"]["n"]
    assert c["ic95"][0] <= c["diferencia"] <= c["ic95"][1]
    assert "holdout" in ev["comparacionMadre"]
    ev_mod.guardar(ev, tmp_path)
    # hija y madre en 2 tramos, más los 2 vecinos de estabilidad de la hija, × 2 símbolos
    assert len((tmp_path / "mediciones.jsonl").read_text().splitlines()) == 12
    assert "Contra la madre" in (tmp_path / "reports" / f"{d['id']}.md").read_text()


def _t(abre, cierra, direccion=1, r=1.0):
    from bt.engine import Trade
    return Trade(direccion=direccion, senal_en=abre, abierto_en=abre, cerrado_en=cierra, entrada=1, stop=0.9,
                 objetivo=None, salida=1, motivo="SL", r_bruto=r, fee_r=0, r_neto=r, mae_r=0, velas=1)


def test_cupo_por_direccion():
    por = {"A": [_t("2020-01-01", "2020-01-05")], "B": [_t("2020-01-02", "2020-01-03")],
           "C": [_t("2020-01-02", "2020-01-04"), _t("2020-01-06", "2020-01-07")],
           "D": [_t("2020-01-02", "2020-01-03", direccion=-1)]}
    out = ev_mod.aplicar_cupo(por, 2)
    assert len(out["A"]) == 1 and len(out["B"]) == 1 and len(out["D"]) == 1
    assert [t.abierto_en for t in out["C"]] == ["2020-01-06"]  # la del 2 encontró el cupo lleno
    assert ev_mod.aplicar_cupo(por, None) is por


def test_peor_caida():
    ts = [_t("1", "1", r=1), _t("2", "2", r=-1), _t("3", "3", r=-2), _t("4", "4", r=3)]
    assert ev_mod.peor_caida(ts) == -3.0


def test_perturbar_parametros():
    p = ev_mod.perturbar({"entrada": 20, "salida": 1, "stop_atr": 2.0, "largo": True, "modo": "x"}, 0.8)
    assert p == {"entrada": 16, "salida": 1, "stop_atr": 1.6, "largo": True, "modo": "x"}
    assert ev_mod.perturbar({"n": 3}, 1.2) == {"n": 4}  # 3.6 → 4
    assert ev_mod.perturbar({"n": 2}, 1.2) == {"n": 3}  # 2.4 redondea a 2: se mueve en 1


def test_estabilidad_se_mide_antes_del_holdout_y_puede_decidir(mundo, tmp_path):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(BASE), cv, cf, base=tmp_path)
    est = ev["estabilidad"]
    assert [v["factor"] for v in est["vecinos"]] == [0.8, 1.2]
    assert est["vecinos"][0]["params"] == {"entrada": 16, "salida": 8}
    assert not any("estabilidad" in c["criterio"] for c in ev["criterios"])  # sin umbral: sólo informa
    ev_mod.guardar(ev, tmp_path)
    assert "Estabilidad de parámetros" in (tmp_path / "reports" / f"{BASE['id']}.md").read_text()
    assert len((tmp_path / "mediciones.jsonl").read_text().splitlines()) == 8  # 2 tramos + 2 vecinos, × 2
    exigente = con(id="2026-11-03-exigente", criterio_aprobacion__estabilidad_minima=50.0)  # imposible
    r = ev_mod.evaluar(desde_dict(exigente), cv, cf, base=tmp_path)
    assert r["veredicto"] == "RECHAZADA" and r["holdout"] is None
    assert any("estabilidad" in m for m in r["motivos"])


def test_familia_por_modulo_cuenta_las_variantes_viejas(mundo, tmp_path):
    cv, cf, _ = mundo
    ev_mod.guardar(ev_mod.evaluar(desde_dict(BASE), cv, cf, base=tmp_path), tmp_path)  # sin `familia`
    nueva = con(id="2026-11-04-nueva", familia="tendencia")
    assert ev_mod.evaluar(desde_dict(nueva), cv, cf, base=tmp_path)["nPruebas"] == 2


def test_correccion_por_numero_de_pruebas(mundo, tmp_path):
    assert round(ev_mod.z_por_pruebas(1), 2) == 1.96 and round(ev_mod.z_por_pruebas(8), 2) == 2.73
    cv, cf, _ = mundo
    d = con(criterio_aprobacion__ajuste_por_pruebas=True)
    uno = ev_mod.evaluar(desde_dict(d), cv, cf, base=tmp_path)
    c = [x for x in uno["criterios"] if x["criterio"].startswith("ajustado")][0]
    assert "1 prueba" in c["criterio"] and "1.96" in c["criterio"]
    muchas = ev_mod.evaluar(desde_dict(con(criterio_aprobacion__ajuste_por_pruebas=True, pruebas_previas=10_000)),
                            cv, cf, base=tmp_path)
    c2 = [x for x in muchas["criterios"] if x["criterio"].startswith("ajustado")][0]
    assert "10001 prueba" in c2["criterio"] and float(c2["criterio"].split("− ")[1].split(" ")[0]) > 4.4


def test_sitio_secciones_de_docs(tmp_path):
    base = tmp_path / "results"
    (base / "reports").mkdir(parents=True)
    (tmp_path / "02-DOCS").mkdir()
    (base / "reports" / "adelante.md").write_text(
        "# Prueba hacia adelante\n\nTexto.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    (tmp_path / "02-DOCS" / "ideas.md").write_text(
        "| # | Idea | a | b | c | Estado |\n|---|---|---|---|---|---|\n| 7 | <b>x</b> | 1 | 2 | 3 | en cola |\n"
        "| 8 | vieja | 1 | 2 | 3 | descartada |\n")
    (tmp_path / "02-DOCS" / "backlog.md").write_text(
        "## Recomendadas para esta semana\n\n1. **B-01** Algo\n\n## Espera tu decisión\n\nNada.\n")
    pagina = sitio.generar(base)
    assert 'href="#adelante"' in pagina and 'id="cola"' in pagina and 'id="backlog"' in pagina
    assert "&lt;b&gt;x&lt;/b&gt;" in pagina and "vieja" not in pagina and "<b>B-01</b>" in pagina


def test_spec_de_medicion_nunca_va_a_approved(mundo, tmp_path):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(con(medicion=True)), cv, cf, base=tmp_path)
    assert ev["veredicto"] == "APROBADA" and ev["soloMedicion"]
    ev_mod.guardar(ev, tmp_path)
    assert not (tmp_path / "approved.json").exists()


def test_solo_desarrollo_sin_medicion_se_rechaza():
    with pytest.raises(SpecInvalida, match="solo_desarrollo"):
        desde_dict(con(solo_desarrollo=True))
    assert desde_dict(con(medicion=True, solo_desarrollo=True)).solo_desarrollo


def test_solo_desarrollo_nunca_mira_el_holdout(mundo, tmp_path, monkeypatch):
    from bt import run as run_mod
    from bt.splits import HOLDOUT_DESDE

    cv, cf, _ = mundo
    llamadas = []
    original = run_mod.correr

    def espia(*a, **k):
        llamadas.append((k.get("holdout"), k.get("hasta")))
        return original(*a, **k)

    monkeypatch.setattr(run_mod, "correr", espia)
    d = con(medicion=True, solo_desarrollo=True, madre={"nombre": "sin tope", "config": {"timeout_velas": 14}})
    ev = ev_mod.evaluar(desde_dict(d), cv, cf, base=tmp_path)
    assert llamadas and all(h is False for h, _ in llamadas)  # incluye la madre y los vecinos de estabilidad
    assert ev["holdout"] is None and "holdout" not in ev["comparacionMadre"] and ev["soloDesarrollo"]
    assert ev["veredicto"] == "NO_CONCLUYENTE" and any("holdout no mirado" in m for m in ev["motivos"])
    assert ev["comparacionMadre"]["desarrollo"]["madre"] == "sin tope"
    assert ev["desarrollo"]["ventana"][1] < str(HOLDOUT_DESDE)[:10]
    ev_mod.guardar(ev, tmp_path)
    assert not (tmp_path / "approved.json").exists()
    # No cuenta como mirada del holdout para la familia.
    assert not any(a["holdoutMirado"] for a in ev_mod.antecedentes(desde_dict(con(id="2026-11-02-otra")), tmp_path))
