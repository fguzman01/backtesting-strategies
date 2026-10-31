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
