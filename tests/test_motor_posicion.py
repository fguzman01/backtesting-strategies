"""Gestión de la posición: trailing desde la entrada, breakeven y salida parcial TP1/TP2."""

import pytest

from bt.engine import Config, es_resuelto, simular, simular_ambos
from conftest import senal, velas

SIN_FEE = Config(fee_pct_por_lado=0.0)


def test_trailing_sube_detras_del_mejor_precio_desde_la_entrada():
    df = velas([(100, 100, 100, 100), (100, 104, 99, 103), (103, 106, 102, 105), (105, 105, 102, 103)])
    s = senal(df, {0: dict(direccion=1, stop=95)})
    s["trailing"] = 3.0
    tr = simular(df, s, SIN_FEE)[0]
    # vela 1: mejor 104 → stop 101 desde la vela 2; vela 2: mejor 106 → stop 103; vela 3 toca 102 → sale en 103
    assert tr.motivo == "SL" and tr.salida == pytest.approx(103)
    assert tr.r_bruto == pytest.approx(0.6)
    assert tr.stop == 95  # el stop registrado es el inicial (el que define 1R)


def test_trailing_rige_desde_la_vela_siguiente_no_en_la_misma():
    # La vela de entrada sube a 104 y baja a 100.5: con trailing 3 el stop sería 101, pero recién rige mañana.
    df = velas([(100, 100, 100, 100), (100, 104, 100.5, 102), (102, 102.5, 101.5, 102)])
    s = senal(df, {0: dict(direccion=1, stop=95)})
    s["trailing"] = 3.0
    tr = simular(df, s, SIN_FEE)
    assert tr[0].motivo == "SIN_RESOLVER"  # ni la vela 1 ni la 2 tocan el stop vigente


def test_trailing_nunca_aleja_el_stop():
    df = velas([(100, 100, 100, 100), (100, 104, 99, 103), (103, 103.5, 101.5, 103), (103, 103, 100.5, 101)])
    s = senal(df, {0: dict(direccion=1, stop=95)})
    s["trailing"] = [3.0, 3.0, 10.0, 10.0]  # la distancia se agranda: el stop no baja de 101
    tr = simular(df, s, SIN_FEE)[0]
    assert tr.motivo == "SL" and tr.salida == pytest.approx(101)


def test_trailing_en_corto():
    df = velas([(100, 100, 100, 100), (100, 101, 96, 97), (97, 98, 94, 95), (95, 98, 95, 97)])
    s = senal(df, {0: dict(direccion=-1, stop=105)})
    s["trailing"] = 3.0
    tr = simular(df, s, SIN_FEE)[0]
    # mejor 96 → stop 99; mejor 94 → stop 97; la vela 3 sube a 98 → sale en 97
    assert tr.motivo == "SL" and tr.salida == pytest.approx(97) and tr.r_bruto == pytest.approx(0.6)


def test_breakeven():
    df = velas([(100, 100, 100, 100), (100, 105.5, 99, 104), (104, 104.5, 99.5, 101)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), Config(0.0, breakeven_r=1.0))[0]
    assert tr.motivo == "SL" and tr.salida == pytest.approx(100) and tr.r_bruto == pytest.approx(0)


def test_breakeven_no_se_activa_sin_llegar():
    df = velas([(100, 100, 100, 100), (100, 104.5, 99, 104), (104, 104.5, 99.5, 101)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), Config(0.0, breakeven_r=1.0))
    assert tr[0].motivo == "SIN_RESOLVER"


def test_tp1_parcial_y_resto_a_breakeven():
    df = velas([(100, 100, 100, 100), (100, 106, 99, 104), (104, 104.5, 99, 101)])
    cfg = Config(0.0, tp1_r=1.0, tp1_cierre=0.5, objetivo_r=3.0)
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), cfg)[0]
    assert tr.motivo == "TP1+SL" and tr.resuelto
    assert tr.r_bruto == pytest.approx(0.5)  # 0.5 × 1R + 0.5 × 0R


def test_tp1_parcial_y_resto_al_objetivo():
    df = velas([(100, 100, 100, 100), (100, 106, 99, 104), (104, 116, 103, 115)])
    cfg = Config(0.0, tp1_r=1.0, tp1_cierre=0.5, objetivo_r=3.0)
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), cfg)[0]
    assert tr.motivo == "TP1+TP" and tr.r_bruto == pytest.approx(2.0)  # 0.5 × 1 + 0.5 × 3


def test_vela_ambigua_con_tp1_y_stop():
    df = velas([(100, 100, 100, 100), (100, 106, 94, 101), (101, 116, 100.5, 115)])
    cfg = Config(0.0, tp1_r=1.0, tp1_cierre=0.5, objetivo_r=3.0)
    m = simular_ambos(df, senal(df, {0: dict(direccion=1, stop=95)}), cfg)
    assert m["conservador"][0].motivo == "SL" and m["conservador"][0].r_bruto == pytest.approx(-1)
    assert m["optimista"][0].motivo == "TP1+TP" and m["optimista"][0].r_bruto == pytest.approx(2.0)


def test_tp1_con_cierre_total_es_un_objetivo():
    df = velas([(100, 100, 100, 100), (100, 106, 99, 104)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), Config(0.0, tp1_r=1.0, tp1_cierre=1.0))[0]
    assert tr.motivo == "TP" and tr.r_bruto == pytest.approx(1.0)


def test_comision_en_r_igual_con_parcial():
    df = velas([(100, 100, 100, 100), (100, 106, 99, 104), (104, 104.5, 99, 101)])
    cfg = Config(0.0005, tp1_r=1.0, tp1_cierre=0.5)
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), cfg)[0]
    assert tr.fee_r == pytest.approx(0.02) and tr.r_neto == pytest.approx(0.5 - 0.02)


def test_tp1_cierre_invalido():
    df = velas([(100, 100, 100, 100)] * 3)
    with pytest.raises(ValueError):
        simular(df, senal(df, {}), Config(tp1_r=1.0, tp1_cierre=0))


def test_es_resuelto():
    assert es_resuelto("TP1+SL") and es_resuelto("TP") and not es_resuelto("SIN_RESOLVER")
    assert not es_resuelto("TP1+SIN_RESOLVER")
