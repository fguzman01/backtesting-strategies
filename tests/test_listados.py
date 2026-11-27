import io
import json
import zipfile

from bt import universo


def _zip(*fechas_ms):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.csv", "open_time,open,high,low,close,volume,close_time,quote_volume\n" + "\n".join(
            f"{t},1,1,1,1,1,{t},1" for t in fechas_ms))
    return buf.getvalue()


DIA = 86_400_000
T0 = 1_600_000_000_000  # 2020-09-13
PREF = universo.PREFIJO


def _falso(monkeypatch, zips):
    """zips: {simbolo: {AAAA-MM: bytes}}; sirve el listado y las descargas sin red."""
    def listar(prefijo):
        if prefijo == PREF:
            return [f"{PREF}{s}/" for s in zips], []
        s = prefijo[len(PREF):].split("/")[0]
        return [], [f"{prefijo}{s}-1d-{m}.zip" for m in zips[s]]

    def get(url):
        clave = url.split("/1d/")[1]
        s, m = clave.split("-1d-")[0], clave[-11:-4]
        return zips[s][m]

    monkeypatch.setattr(universo, "_listar", listar)
    monkeypatch.setattr(universo, "_get", get)


ZIPS = {
    "NEWUSDT": {"2020-10": _zip(T0 + 20 * DIA, T0 + 21 * DIA), "2020-09": _zip(T0 + 5 * DIA, T0 + 6 * DIA)},
    "LUNAUSDT": {"2021-01": _zip(T0 + 130 * DIA)},  # retirado: igual entra
    "USDCUSDT": {"2020-09": _zip(T0)},              # estable: fuera
    "NVDAUSDT": {"2020-09": _zip(T0)},              # no cripto: fuera
    "BTCUSDT_230331": {"2020-09": _zip(T0)},        # trimestral: fuera
}


def test_fecha_listado_es_la_primera_vela_con_retirados_y_sin_excluidos(monkeypatch):
    _falso(monkeypatch, ZIPS)
    out = universo.fechas_listado()
    assert out == {"LUNAUSDT": "2021-01-21", "NEWUSDT": "2020-09-18"}
    assert list(out) == sorted(out)


def test_listados_determinista_e_incremental(monkeypatch, tmp_path):
    _falso(monkeypatch, ZIPS)
    ruta = tmp_path / "l.json"
    universo.construir_listados(ruta)
    primero = ruta.read_text()
    universo.construir_listados(ruta)
    assert ruta.read_text() == primero
    # un símbolo ya conocido no se vuelve a bajar
    bajados = []
    monkeypatch.setattr(universo, "fecha_listado", lambda s: bajados.append(s))
    universo.fechas_listado(existentes=json.loads(primero))
    assert bajados == []


def test_tabla_dinamica_no_cambia():
    vol = {"A": {m: 1.0 for m in ("2020-01", "2020-02", "2020-03", "2020-04")}}
    assert universo.armar_tabla(vol, "2020-05") == {"2020-04": ["A"], "2020-05": ["A"]}
