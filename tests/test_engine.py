import pytest

from bt.engine import Config, simular, simular_ambos
from conftest import senal, velas

SIN_FEE = Config(fee_pct_por_lado=0.0)


def test_largo_toca_objetivo_entra_en_la_apertura_siguiente():
    df = velas([(100, 101, 99, 100), (100, 103, 99.5, 102), (102, 111, 101, 110)])
    t = simular(df, senal(df, {0: dict(direccion=1, stop=95, objetivo=110)}), SIN_FEE)
    assert len(t) == 1
    tr = t[0]
    assert tr.entrada == 100 and tr.abierto_en.startswith("2024-01-02")
    assert tr.motivo == "TP" and tr.salida == 110
    assert tr.r_bruto == pytest.approx(2.0)  # (110-100)/5
    assert tr.velas == 2


def test_comision_en_r_depende_del_stop():
    df = velas([(100, 101, 99, 100), (100, 103, 99.5, 102), (102, 111, 101, 110)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95, objetivo=110)}), Config())[0]
    # 0.0005 * 2 * 100 / 5 = 0.02R
    assert tr.fee_r == pytest.approx(0.02)
    assert tr.r_neto == pytest.approx(2.0 - 0.02)


def test_vela_ambigua_conservador_pierde_optimista_gana():
    df = velas([(100, 101, 99, 100), (100, 100.5, 99.5, 100), (100, 111, 94, 100)])
    s = senal(df, {0: dict(direccion=1, stop=95, objetivo=110)})
    m = simular_ambos(df, s, SIN_FEE)
    assert m["conservador"][0].motivo == "SL" and m["conservador"][0].r_bruto == pytest.approx(-1)
    assert m["optimista"][0].motivo == "TP" and m["optimista"][0].r_bruto == pytest.approx(2)


def test_gap_por_debajo_del_stop_sale_a_la_apertura():
    df = velas([(100, 101, 99, 100), (100, 101, 99, 100), (90, 92, 88, 91)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), SIN_FEE)[0]
    assert tr.motivo == "SL" and tr.salida == 90
    assert tr.r_bruto == pytest.approx(-2.0)  # peor que -1R: el gap no respeta el stop


def test_corto_simetrico():
    df = velas([(100, 101, 99, 100), (100, 101, 97, 98), (98, 99, 89, 90)])
    tr = simular(df, senal(df, {0: dict(direccion=-1, stop=105, objetivo=90)}), SIN_FEE)[0]
    assert tr.motivo == "TP" and tr.r_bruto == pytest.approx(2.0)
    assert tr.mae_r == pytest.approx(0.2)  # máximo 101 contra entrada 100, riesgo 5


def test_timeout_cierra_al_cierre():
    df = velas([(100, 101, 99, 100)] + [(100, 101, 99, 100.5)] * 4)
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), Config(0.0, timeout_velas=3))[0]
    assert tr.motivo == "TIMEOUT" and tr.velas == 3 and tr.salida == 100.5


def test_salida_por_regla_en_la_apertura_siguiente():
    df = velas([(100, 101, 99, 100), (100, 102, 99, 101), (101, 104, 100, 103), (104, 105, 103, 104)])
    s = senal(df, {0: dict(direccion=1, stop=95), 2: dict(salida=True)})
    tr = simular(df, s, SIN_FEE)[0]
    assert tr.motivo == "SALIDA" and tr.salida == 104 and tr.cerrado_en.startswith("2024-01-04")


def test_objetivo_en_multiplos_de_r():
    df = velas([(100, 101, 99, 100), (100, 108, 99, 107)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), Config(0.0, objetivo_r=1.5))[0]
    assert tr.objetivo == pytest.approx(107.5) and tr.motivo == "TP"


def test_deslizamiento_mueve_la_entrada_no_filtra():
    df = velas([(100, 101, 99, 100), (100, 103, 99.5, 102), (102, 111, 101, 110)])
    tr = simular(df, senal(df, {0: dict(direccion=1, stop=95, objetivo=110)}), Config(0.0, 0.01))[0]
    assert tr.entrada == pytest.approx(101) and tr.motivo == "TP"


def test_stop_del_lado_equivocado_no_es_trade():
    df = velas([(100, 101, 99, 100), (94, 95, 93, 94), (94, 95, 93, 94)])
    t = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), SIN_FEE)
    assert t[0].motivo == "STOP_INVALIDO" and not t[0].resuelto and t[0].r_neto == 0


def test_posicion_abierta_al_final_queda_sin_resolver():
    df = velas([(100, 101, 99, 100), (100, 101, 99, 100), (100, 101, 99, 100)])
    t = simular(df, senal(df, {0: dict(direccion=1, stop=95)}), SIN_FEE)
    assert t[-1].motivo == "SIN_RESOLVER" and not t[-1].resuelto


def test_una_posicion_a_la_vez():
    df = velas([(100, 101, 99, 100)] * 2 + [(100, 111, 99, 110)] + [(110, 111, 109, 110)] * 2)
    s = senal(df, {0: dict(direccion=1, stop=95, objetivo=110), 1: dict(direccion=1, stop=95, objetivo=110)})
    t = simular(df, s, SIN_FEE)
    assert len(t) == 1  # la señal de la vela 1 llega con la posición abierta


def test_indice_distinto_falla():
    df = velas([(100, 101, 99, 100)] * 3)
    with pytest.raises(ValueError):
        simular(df, senal(df, {}).iloc[1:], SIN_FEE)
