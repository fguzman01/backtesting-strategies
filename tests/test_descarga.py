import datetime as dt
import io
import re
import zipfile

from bt import data


def _zip_mes(y, m):
    buf = io.BytesIO()
    filas = []
    d = dt.date(y, m, 1)
    while d.month == m:
        t = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.UTC).timestamp() * 1000)
        filas.append(f"{t},1,2,0.5,1.5,10,0,0,0,0,0,0")
        d += dt.timedelta(days=1)
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.csv", "\n".join(filas))
    return buf.getvalue()


def test_descarga_incremental_y_completa(tmp_path, monkeypatch):
    pedidos = []
    hoy = dt.datetime.now(dt.UTC).date()

    def falso_get(url):
        pedidos.append(url)
        mm = re.search(r"-(\d{4})-(\d{2})\.zip$", url)
        if not mm or "/daily/" in url:
            return None
        y, m = int(mm[1]), int(mm[2])
        return None if (y, m) >= (hoy.year, hoy.month) else _zip_mes(y, m)  # el mes en curso aún no existe

    monkeypatch.setattr(data, "_get", falso_get)
    ruta = data.descargar("XUSDT", "1d", "2024-01", base=tmp_path)
    primera = len([u for u in pedidos if "/monthly/" in u])
    df = data.desde_csv(ruta)
    assert df.index[0].date() == dt.date(2024, 1, 1)
    assert not df.index.has_duplicates and df.index.is_monotonic_increasing

    pedidos.clear()
    data.descargar("XUSDT", "1d", "2024-01", base=tmp_path)
    segunda = len([u for u in pedidos if "/monthly/" in u])
    assert segunda <= 3 < primera  # sólo los últimos meses
    assert data.desde_csv(ruta).equals(df)


def test_calidad_detecta_huecos_duplicados_y_saltos():
    import pandas as pd
    idx = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-05"], utc=True)
    df = pd.DataFrame({"close": [1.0, 1.1, 1.1, 2.0], "volume": [1, 0, 1, 1]}, index=idx)
    c = data.calidad(df, 1440)
    assert c["duplicadas"] == 1 and c["huecos"] == 2 and c["volumenCero"] == 1 and c["saltos"] == 1
