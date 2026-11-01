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
    "criterio_aprobacion": {"n_minimo": 10, "ic95_excluye_cero": False, "concluyente": False,
                            "supera_nulo_p95": False, "holdout": {"avgRNeto_positivo": True}},
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
    ev = ev_mod.evaluar(desde_dict(BASE), cv, cf)
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
    assert len(filas) == 4  # 2 símbolos × (desarrollo + holdout)
    assert ev_mod.evaluada("2026-11-01-prueba", tmp_path)


def test_si_falla_desarrollo_el_holdout_no_se_mira(mundo, tmp_path):
    cv, cf, _ = mundo
    d = con(criterio_aprobacion__supera_nulo_p95=True, criterio_aprobacion__n_minimo=10)
    d["criterio_aprobacion"]["tramos_positivos_minimo"] = 5  # imposible: hay como mucho 4 tramos
    ev = ev_mod.evaluar(desde_dict(d), cv, cf)
    assert ev["veredicto"] == "RECHAZADA" and ev["holdout"] is None
    assert any("tramos positivos" in m for m in ev["motivos"])
    ev_mod.guardar(ev, tmp_path)
    assert not (tmp_path / "approved.json").exists()
    assert "No se miró" in (tmp_path / "reports" / f"{d['id']}.md").read_text()


def test_muestra_chica_es_no_concluyente(mundo):
    cv, cf, _ = mundo
    ev = ev_mod.evaluar(desde_dict(con(criterio_aprobacion__n_minimo=100000)), cv, cf)
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
    ev = ev_mod.evaluar(desde_dict(BASE), cv, cf)
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
