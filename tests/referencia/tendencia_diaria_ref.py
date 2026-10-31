"""Oráculo de prueba: la lógica de `fguzman01/btc-signal-web/scripts/backtest-tendencia-diaria.py`
(commit fa74ed8), con la que se aprobó TREND_1D el 2026-10-20.

Se copian `indicadores` y `operar` sin cambiar reglas; sólo se pasaron a parámetros las constantes
globales (velas, funding, tramo, cortes) para poder llamarlas desde los tests. No se usa en
producción: existe para comprobar que `bt.engine` + `bt.strategies.tendencia_donchian` dan
exactamente las mismas operaciones.
"""

DIA = 86_400_000


def indicadores(v, ema_n=200, atr_n=20):
    n = len(v)
    ema, atr = [None] * n, [None] * n
    k = 2 / (ema_n + 1)
    e = None
    for i, (_, _, _, _, c) in enumerate(v):
        e = c if e is None else e + k * (c - e)
        if i >= ema_n - 1:
            ema[i] = e
    tr = [v[0][2] - v[0][3]] + [
        max(v[i][2] - v[i][3], abs(v[i][2] - v[i - 1][4]), abs(v[i][3] - v[i - 1][4])) for i in range(1, n)
    ]
    a = None
    for i in range(n):  # Wilder: siembra con SMA y suaviza
        if i == atr_n - 1:
            a = sum(tr[:atr_n]) / atr_n
        elif i >= atr_n:
            a = (a * (atr_n - 1) + tr[i]) / atr_n
        atr[i] = a
    return ema, atr


def operar(v, fund, tramo, corte, fin, entrada_n=20, salida_n=10, bar=DIA, costo_lado=0.001,
           ema_n=200, atr_n=20, stop_atr=2.0):
    ema, atr = indicadores(v, ema_n, atr_n)
    ops = []
    inicio = max(ema_n, entrada_n + 1)
    limite = corte if tramo == "desarrollo" else fin
    desde_entrada = 0 if tramo == "desarrollo" else corte
    pos = None
    salir_en_apertura = False

    def cerrar(precio, t_out, motivo):
        d = pos["dir"]
        bruto = d * (precio - pos["entrada"]) / pos["entrada"]
        f = d * fund(pos["t_in"], t_out)
        neto = bruto - 2 * costo_lado - f
        ops.append({"dir": d, "t_in": pos["t_in"], "t_out": t_out, "entrada": pos["entrada"],
                    "salida": precio, "r": neto * pos["entrada"] / pos["r_precio"], "motivo": motivo})

    for j in range(inicio, len(v)):
        t, o, h, l, c = v[j]  # noqa: E741
        if t + bar > limite:
            break
        if pos:
            d = pos["dir"]
            if salir_en_apertura:
                cerrar(o, t, "CANAL"); pos = None; salir_en_apertura = False  # noqa: E702
            elif (d > 0 and o <= pos["stop"]) or (d < 0 and o >= pos["stop"]):
                cerrar(o, t, "STOP_APERTURA"); pos = None  # noqa: E702
            elif (d > 0 and l <= pos["stop"]) or (d < 0 and h >= pos["stop"]):
                cerrar(pos["stop"], t + bar // 2, "STOP"); pos = None  # noqa: E702
        if pos:
            ll = min(x[3] for x in v[j - salida_n:j]); hh = max(x[2] for x in v[j - salida_n:j])  # noqa: E702
            if (pos["dir"] > 0 and c < ll) or (pos["dir"] < 0 and c > hh):
                salir_en_apertura = True
        if (not pos and j + 1 < len(v) and v[j + 1][0] >= desde_entrada and v[j + 1][0] + bar <= limite
                and ema[j] and atr[j]):
            hh20 = max(x[2] for x in v[j - entrada_n:j]); ll20 = min(x[3] for x in v[j - entrada_n:j])  # noqa: E702
            d = 1 if (c > hh20 and c > ema[j]) else -1 if (c < ll20 and c < ema[j]) else 0
            if d:
                e = v[j + 1][1]
                r_precio = stop_atr * atr[j]
                pos = {"dir": d, "entrada": e, "stop": e - d * r_precio, "r_precio": r_precio,
                       "t_in": v[j + 1][0], "i_in": j + 1}
    if pos:  # cierre forzado al último cierre del tramo
        ult = max(k for k in range(len(v)) if v[k][0] + bar <= limite)
        cerrar(v[ult][4], v[ult][0] + bar, "FIN_DE_TRAMO")
    return ops
