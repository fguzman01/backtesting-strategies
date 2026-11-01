import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from bt import auditoria
from bt.auditoria import AVISO, FALLA, OK
from bt.evaluar import anotar_en_decisiones, linea_decisiones

SPEC = {
    "id": "2026-11-01-x",
    "estado": "pre-registrada",
    "hipotesis": "Algo persiste. Más texto.",
    "horizonte": {"tipo": "diario"},
    "estrategia": {"modulo": "tendencia_donchian", "params": {}},
    "universo": {"mercado": "futures", "simbolos": ["AUSDT"], "intervalo": "1d"},
    "config": {"timeout_velas": 7},
    "criterio_aprobacion": {"n_minimo": 10},
}


def ev(sid="2026-11-01-x", veredicto="RECHAZADA", holdout=None, dev_ok=False, modulo="tendencia_donchian"):
    s = copy.deepcopy(SPEC) | {"id": sid}
    s["estrategia"]["modulo"] = modulo
    g = {"n": 50, "avgRNeto": 0.1, "ic95": [-0.1, 0.3]}
    return {
        "id": sid, "fecha": "2026-11-01T00:00:00+00:00", "veredicto": veredicto, "spec": s,
        "motivos": [] if dev_ok else ["desarrollo: falla «x» (y)"],
        "criterios": [{"criterio": "x", "valor": "y", "ok": dev_ok}],
        "desarrollo": {"global": g}, "holdout": holdout,
    }


def git(raiz, *a):
    subprocess.run(["git", "-C", str(raiz), *a], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    for d in ("specs", "results/evaluaciones", "src/bt/strategies", "tests", "02-DOCS"):
        (tmp_path / d).mkdir(parents=True)
    tabla = "# D\n\n| Pregunta | Veredicto | Cuándo | Reporte |\n|---|---|---|---|\n"
    (tmp_path / "02-DOCS" / "decisiones.md").write_text(tabla)
    return tmp_path


def escribir_spec(raiz, d=SPEC):
    (raiz / "specs" / f"{d['id']}.yaml").write_text(yaml.safe_dump(d))


def escribir_ev(raiz, e):
    (raiz / "results" / "evaluaciones" / f"{e['id']}.json").write_text(json.dumps(e))


def por_nombre(chequeos):
    return {c.nombre: c for c in chequeos}


def test_repo_limpio_pasa(repo):
    escribir_spec(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "spec")
    e = ev()
    escribir_ev(repo, e)
    anotar_en_decisiones(e, repo / "02-DOCS" / "decisiones.md")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "evaluación")
    ch = auditoria.auditar(repo)
    assert all(c.estado != FALLA for c in ch), auditoria.informe_md(ch)
    assert por_nombre(ch)["Pre-registro antes de evaluar"].estado == OK
    assert por_nombre(ch)["Brain actualizado con cada evaluación"].estado == OK


def test_spec_editada_despues_de_evaluar(repo):
    escribir_spec(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "spec")
    escribir_ev(repo, ev())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "evaluación")
    d = copy.deepcopy(SPEC)
    d["criterio_aprobacion"]["n_minimo"] = 5  # aflojar el criterio después de ver el número
    escribir_spec(repo, d)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "ajuste")
    c = por_nombre(auditoria.auditar(repo))["Pre-registro antes de evaluar"]
    assert c.estado == FALLA and "modificó después" in c.detalle[0]


def test_spec_y_evaluacion_en_el_mismo_commit(repo):
    escribir_spec(repo)
    escribir_ev(repo, ev())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "todo junto")
    c = por_nombre(auditoria.auditar(repo))["Pre-registro antes de evaluar"]
    assert c.estado == FALLA and "antes de la evaluación" in c.detalle[0]


def test_holdout_sin_pasar_desarrollo(repo):
    escribir_ev(repo, ev(holdout={"global": {"n": 5}}, dev_ok=False))
    c = por_nombre(auditoria.auditar(repo))["Holdout: sólo si pasa desarrollo, una vez"]
    assert c.estado == FALLA


def test_holdout_mirado_dos_veces(repo):
    escribir_ev(repo, ev(veredicto="APROBADA", holdout={"global": {"n": 5}}, dev_ok=True))
    fila = {"nota": "evaluacion 2026-11-01-x (holdout)"}
    (repo / "results" / "mediciones.jsonl").write_text(json.dumps(fila) + "\n" + json.dumps(fila) + "\n")
    c = por_nombre(auditoria.auditar(repo))["Holdout: sólo si pasa desarrollo, una vez"]
    assert c.estado == FALLA and "2 veces" in c.detalle[0]


def test_approved_inconsistente(repo):
    (repo / "results" / "approved.json").write_text(json.dumps({"estrategias": [{"id": "inventada"}]}))
    escribir_ev(repo, ev(sid="2026-11-02-y", veredicto="APROBADA", holdout={"global": {}}, dev_ok=True))
    c = por_nombre(auditoria.auditar(repo))["approved.json coincide con las evaluaciones"]
    assert c.estado == FALLA
    assert any("inventada" in d for d in c.detalle) and any("PR pendiente" in d for d in c.detalle)


def test_estrategia_sin_test_de_lookahead(repo):
    (repo / "src/bt/strategies/nueva.py").write_text("def senales(df): ...\n")
    (repo / "tests/test_otra.py").write_text("chequear_lookahead(otra.senales, df)\n")
    c = por_nombre(auditoria.auditar(repo))["Toda estrategia tiene test de look-ahead"]
    assert c.estado == FALLA and "nueva" in c.detalle[0]
    (repo / "tests/test_nueva.py").write_text("chequear_lookahead(nueva.senales, df)\n")
    assert por_nombre(auditoria.auditar(repo))["Toda estrategia tiene test de look-ahead"].estado == OK


def test_bitacora_no_determinista(repo):
    base = {"commit": "abc", "strategy": "s", "symbol": "X", "interval": "1d", "desde": "a", "hasta": "b",
            "config": {"fee": 1}, "n": 10}
    filas = [base | {"avgRNeto": 0.1}, base | {"avgRNeto": 0.2}, base | {"commit": "abc+cambios", "avgRNeto": 9}]
    (repo / "results" / "mediciones.jsonl").write_text("\n".join(json.dumps(f) for f in filas) + "\n")
    c = por_nombre(auditoria.auditar(repo))["Bitácora: misma config, mismo número"]
    assert c.estado == FALLA and len(c.detalle) == 1


def test_muchas_variantes_avisa_data_snooping(repo):
    for i in range(5):
        escribir_ev(repo, ev(sid=f"2026-11-0{i + 1}-v{i}"))
    c = por_nombre(auditoria.auditar(repo))["Cuántas pruebas se hicieron (data snooping)"]
    assert c.estado == AVISO and "5 variantes" in c.detalle[1]


def test_linea_de_decisiones_y_no_duplica(repo):
    e = ev()
    linea = linea_decisiones(e)
    assert linea.startswith("| Algo persiste (`2026-11-01-x`) | **RECHAZADA.**")
    assert "No pasa: «x» (y)" in linea and "falla" not in linea
    ruta = repo / "02-DOCS" / "decisiones.md"
    anotar_en_decisiones(e, ruta)
    anotar_en_decisiones(e, ruta)
    assert ruta.read_text().count("`2026-11-01-x`") == 1


def test_cli_sale_con_1_si_hay_violaciones(repo, capsys):
    (repo / "src/bt/strategies/nueva.py").write_text("")
    salida = repo / "out.json"
    assert auditoria.main(["--raiz", str(repo), "--json", str(salida)]) == 1
    assert json.loads(salida.read_text())[4]["estado"] == FALLA
    assert "violaciones" in capsys.readouterr().out


def test_el_repo_real_cumple():
    assert all(c.estado != FALLA for c in auditoria.auditar(Path("."))), auditoria.informe_md(
        auditoria.auditar(Path(".")))


def _con_dev(e, ventana, ic, tramos=(), calidad=None, nulo=None):
    e["desarrollo"] = {"global": {"n": 50, "avgRNeto": 0.05, "ic95": ic}, "ventana": ventana,
                       "porTramo": [{"n": n} for n in tramos], "nulo": {"p95": nulo}}
    if calidad is not None:
        e["desarrollo"]["calidadDatos"] = calidad
    return e


def test_ventana_corta_sin_bajista_y_poca_potencia(repo):
    escribir_ev(repo, _con_dev(ev(), ["2023-01-01", "2025-09-01"], [-0.2, 0.3], tramos=(10, 40)))
    c = por_nombre(auditoria.auditar(repo))["Ventana y potencia estadística"]
    texto = " ".join(c.detalle)
    assert c.estado == AVISO
    assert "años" in texto and "2022" in texto and "comisión" in texto and "tramo(s)" in texto


def test_ventana_buena_pasa(repo):
    escribir_ev(repo, _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.15], tramos=(60, 60)))
    assert por_nombre(auditoria.auditar(repo))["Ventana y potencia estadística"].estado == OK


def test_saltos_grandes_no_son_error(repo):
    rally = {"AUSDT": {"duplicadas": 0, "saltos": 3, "inconsistentes": 0, "huecosPct": 0}}
    escribir_ev(repo, _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.1], calidad=rally))
    assert por_nombre(auditoria.auditar(repo))["Calidad de los datos usados"].estado == OK


def test_velas_imposibles_son_error(repo):
    malo = {"AUSDT": {"duplicadas": 0, "saltos": 0, "inconsistentes": 1, "huecosPct": 0}}
    escribir_ev(repo, _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.1], calidad=malo))
    assert por_nombre(auditoria.auditar(repo))["Calidad de los datos usados"].estado == FALLA


def test_casi_todo_por_timeout_avisa(repo):
    e = _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.1])
    e["desarrollo"]["global"]["porMotivo"] = {"TIMEOUT": 30, "SL": 20}
    escribir_ev(repo, e)
    c = por_nombre(auditoria.auditar(repo))["La regla de salida actúa (no todo es timeout)"]
    assert c.estado == AVISO and "60%" in c.detalle[0]
    e["desarrollo"]["global"]["porMotivo"] = {"TIMEOUT": 10, "SL": 40}
    escribir_ev(repo, e)
    assert por_nombre(auditoria.auditar(repo))["La regla de salida actúa (no todo es timeout)"].estado == OK


def test_calidad_de_datos(repo):
    malo = {"AUSDT": {"duplicadas": 2, "saltos": 0, "huecosPct": 0}}
    escribir_ev(repo, _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.1], calidad=malo))
    assert por_nombre(auditoria.auditar(repo))["Calidad de los datos usados"].estado == FALLA
    huecos = {"AUSDT": {"duplicadas": 0, "saltos": 0, "huecosPct": 2.0, "huecos": 40}}
    escribir_ev(repo, _con_dev(ev(), ["2020-01-01", "2025-09-08"], [0.01, 0.1], calidad=huecos))
    assert por_nombre(auditoria.auditar(repo))["Calidad de los datos usados"].estado == AVISO


def test_rechazo_al_borde(repo):
    e = _con_dev(ev(), ["2020-01-01", "2025-09-08"], [-0.01, 0.2])
    e["criterios"] = [{"criterio": "avgR neto > 0 y ±2 EE fuera del cero", "valor": "", "ok": False},
                      {"criterio": "n ≥ 10", "valor": 50, "ok": True}]
    escribir_ev(repo, e)
    c = por_nombre(auditoria.auditar(repo))["Rechazos al borde (para revisión con criterio)"]
    assert c.estado == AVISO and "0.010R" in c.detalle[0]
    e["desarrollo"]["global"]["ic95"] = [-0.2, 0.2]  # lejos del borde
    escribir_ev(repo, e)
    assert por_nombre(auditoria.auditar(repo))["Rechazos al borde (para revisión con criterio)"].estado == OK


def test_desgaste_del_holdout(repo):
    for i in range(10):
        escribir_ev(repo, ev(sid=f"2026-11-{i + 10}-h{i}", veredicto="APROBADA", holdout={"global": {}}, dev_ok=True))
    c = por_nombre(auditoria.auditar(repo))["Desgaste del holdout"]
    assert c.estado == AVISO and "renovación" in c.detalle[1]


def test_clon_superficial_no_inventa_violaciones(repo, tmp_path_factory):
    escribir_spec(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "spec")
    escribir_ev(repo, ev())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "evaluación")
    clon = tmp_path_factory.mktemp("clon") / "r"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(clon)], check=True)
    c = por_nombre(auditoria.auditar(clon))["Pre-registro antes de evaluar"]
    assert c.estado == AVISO and "no se pudo verificar" in c.detalle[0]
