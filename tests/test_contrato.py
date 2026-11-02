import copy
import json
from pathlib import Path

from bt.contrato import main, validar

VALIDA = {"estrategias": [{
    "id": "x", "estrategia": "m", "params": {}, "mercado": "futures", "intervalo": "4h", "simbolos": ["BTCUSDT"],
    "config": {"timeout_velas": 42}, "desarrollo": {"n": 10, "avgRNeto": 0.1, "ic95": [0.0, 0.2]},
    "holdout": {"n": 5, "avgRNeto": 0.05, "ic95": None},
    "aprobada_en": "2026-11-02", "commit": "abc", "reporte": "r.md",
    "nivel": "observacion", "n_pruebas": 2, "holdout_contaminado": True,
}]}


def test_valida():
    assert validar(VALIDA) == []


def test_detecta_campos_faltantes_y_tipos():
    d = copy.deepcopy(VALIDA)
    del d["estrategias"][0]["intervalo"]
    d["estrategias"][0]["holdout"]["ic95"] = [0.1]
    d["estrategias"][0]["config"] = {}
    d["estrategias"].append(copy.deepcopy(VALIDA["estrategias"][0]))
    errores = " ".join(validar(d))
    assert "intervalo" in errores and "ic95" in errores and "timeout_velas" in errores and "repetido" in errores


def test_nivel_y_cupo():
    d = copy.deepcopy(VALIDA)
    d["estrategias"][0]["nivel"] = "real"
    d["estrategias"][0]["max_por_direccion"] = 0
    errores = " ".join(validar(d))
    assert "nivel" in errores and "max_por_direccion" in errores


def test_el_approved_json_del_repo_cumple():
    ruta = Path("results/approved.json")
    if ruta.exists():
        assert validar(json.loads(ruta.read_text())) == []
    assert main([str(ruta)]) == 0
