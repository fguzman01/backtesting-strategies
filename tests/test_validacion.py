from bt import validacion
from bt.validacion import CASOS, Resultado


def test_tolerancias():
    c = CASOS[0]  # 567 trades, +0.545
    assert Resultado(c, 567, 0.545, None, []).reproduce
    assert Resultado(c, 578, 0.56, None, []).reproduce  # dentro de 2% y 0.02R
    assert not Resultado(c, 600, 0.545, None, []).reproduce
    assert not Resultado(c, 567, 0.50, None, []).reproduce
    assert not Resultado(c, 567, 0.545, None, ["BTCUSDT"]).reproduce


def test_sin_datos_no_reproduce_y_lo_dice(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert validacion.main(["--caso", "oro"]) == 1
    assert "faltan datos: PAXGUSDT" in capsys.readouterr().out
