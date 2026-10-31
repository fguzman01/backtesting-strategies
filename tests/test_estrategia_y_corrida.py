import json

import numpy as np
import pandas as pd
import pytest

from bt import bitacora, data, run
from bt.checks import chequear_comision, chequear_determinismo, chequear_lookahead
from bt.engine import Config
from bt.strategies import cargar, donchian_breakout, tendencia_donchian


def test_donchian_sin_lookahead(paseo):
    assert chequear_lookahead(donchian_breakout.senales, paseo) == []
    assert chequear_lookahead(donchian_breakout.senales, paseo, cortos=True) == []


def test_tendencia_donchian_sin_lookahead(paseo):
    assert chequear_lookahead(tendencia_donchian.senales, paseo) == []
    assert chequear_lookahead(tendencia_donchian.senales, paseo, entrada=55, salida=20) == []


def test_el_chequeo_caza_una_estrategia_que_mira_el_futuro(paseo):
    def tramposa(df):
        s = pd.DataFrame(index=df.index)
        s["direccion"] = (df["close"].shift(-1) > df["close"]).astype(int)  # mira mañana
        s["stop"] = df["close"] * 0.95
        return s

    assert chequear_lookahead(tramposa, paseo)


def test_determinismo_y_comision(paseo):
    assert chequear_determinismo(donchian_breakout.senales, paseo, Config()) == []
    assert chequear_comision(Config(fee_pct_por_lado=0)) != []


def test_cargar_estrategia_por_nombre():
    assert cargar("donchian_breakout") is donchian_breakout.senales
    with pytest.raises(ValueError):
        cargar("../os")


def test_corrida_de_punta_a_punta_respeta_el_holdout(paseo, tmp_path):
    r = run.correr("donchian_breakout", paseo, simbolo="BTCUSDT", intervalo="1d", desde="2020-01-01")
    f = r.fila
    assert f["tramo"] == "desarrollo"
    assert pd.Timestamp(f["hasta"]) < pd.Timestamp("2025-09-09", tz="UTC")
    assert any("recortada" in a for a in f["avisos"])
    # Ningún trade abre antes de la ventana ni después del corte.
    for t in r.trades["conservador"]:
        assert pd.Timestamp("2020-01-01", tz="UTC") < pd.Timestamp(t.abierto_en) < pd.Timestamp(
            "2025-09-09", tz="UTC"
        )
    assert f["n"] > 10 and f["config"]["fee_pct_por_lado"] == 0.0005

    ruta = tmp_path / "m.jsonl"
    bitacora.registrar(f, ruta)
    bitacora.registrar(f, ruta)
    filas = bitacora.leer(ruta)
    assert len(filas) == 2 and filas[0]["avgRNeto"] == pytest.approx(f["avgRNeto"])
    json.dumps(filas[0])  # serializable

    # Misma corrida, mismo número.
    r2 = run.correr("donchian_breakout", paseo, simbolo="BTCUSDT", intervalo="1d", desde="2020-01-01")
    assert r2.fila["avgRNeto"] == f["avgRNeto"] and r2.fila["n"] == f["n"]
    assert "concluyente" in run.resumen(r)


def test_cli_con_csv_local(paseo, tmp_path, capsys, monkeypatch):
    ruta = data.ruta_local("BTCUSDT", "1d", "futures", tmp_path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    out = paseo.copy()
    out.insert(0, "time", (paseo.index.astype("int64") // 10**6).astype(np.int64))
    out.to_csv(ruta, index=False)
    assert data.desde_csv(ruta)["close"].iloc[-1] == pytest.approx(paseo["close"].iloc[-1])

    monkeypatch.chdir(tmp_path)
    run.main(["donchian_breakout", "BTCUSDT", "1d", "--datos", str(tmp_path), "-p", "entrada=55",
              "--nota", "test"])
    assert "donchian_breakout BTCUSDT 1d" in capsys.readouterr().out
    filas = bitacora.leer(tmp_path / "results" / "mediciones.jsonl")
    assert filas[-1]["config"]["params"] == {"entrada": 55} and filas[-1]["nota"] == "test"


def test_parsear_zip_normaliza_microsegundos():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "x.csv",
            "open_time,open,high,low,close,volume\n"
            "1735689600000000,1,2,0.5,1.5,10,0,0,0,0,0,0\n"
            "1735776000000,1.5,2,1,1.8,11,0,0,0,0,0,0\n",
        )
    filas = data.parsear_zip(buf.getvalue())
    assert sorted(filas) == [1735689600000, 1735776000000]
    assert filas[1735689600000] == ["1735689600000", "1", "2", "0.5", "1.5", "10"]
