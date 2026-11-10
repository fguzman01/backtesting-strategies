# 2026-11-10-continuacion-volumen-4h — RECHAZADA

- **Estrategia:** `continuacion_volumen` {"ventana_vol": 180, "pct_volumen": 0.9, "retorno_velas": 6, "umbral_atr": 2.0, "atr_n": 14, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 4h · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-10T06:44:54+00:00 · commit `52149b0`

## Hipótesis

Mecanismo: el flujo informado o forzado que llega con volumen inusual se incorpora al precio de a poco; quien pierde es el que provee liquidez a destiempo contra ese flujo. El volumen solo casi no predice; la interacción volumen × retorno previo sí (resumen del paper, efecto a 12–24 h). Regla, UNA sola configuración fijada antes de correr: en 4h, volumen de la vela > percentil 90 del volumen de las 180 velas anteriores (30 días) Y movimiento de las últimas 6 velas (24 h) >= 2 ATR14 en valor absoluto; entrar en la dirección del movimiento en la apertura siguiente. Stop inicial 2 ATR y trailing 2 ATR desde la entrada (lo mueve el motor); sin objetivo. Tope de 18 velas (3 días): el efecto reportado es de 12–24 h, así que un tope largo sólo diluiría, y con trailing la mediana esperada queda por debajo de los 7 días del alcance (la lección de chandelier-14d). La comisión en R es chica porque el stop es de varios porcentos en 4h (0.1% por lado = comisión + deslizamiento, que aquí importa: se entra justo tras un pico de volumen). Universo dinámico top 20 (sin sesgo de supervivencia). Cupo 3 por dirección como TREND_4H. La madre de control es TREND_4H con tope de 7 días: si la continuación por volumen no le gana a un Donchian común, no agrega nada. Una sola idea: ningún umbral se elige mirando datos; la estabilidad ×0.8/×1.2 se mide sola. Riesgos: evidencia C sólo por resumen, el efecto puede ser más corto que una vela de 4h, y solapa con TREND_4H (un movimiento de 2 ATR con volumen suele ser también una ruptura de Donchian).

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 2780 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | -0.046 [-0.087, -0.006] | ❌ |
| ajustado por 1 prueba(s) de la familia: avgR − 1.96 EE > 0 | -0.046 − 1.96×0.020 = -0.086 | ❌ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 0/4 | ❌ |
| supera el percentil 95 del control nulo | -0.046 vs p95 +0.011 | ❌ |
| alcance: duración mediana ≤ 7 días | 1.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (-0.046 [-0.087, -0.006]); desarrollo: falla «ajustado por 1 prueba(s) de la familia: avgR − 1.96 EE > 0» (-0.046 − 1.96×0.020 = -0.086); desarrollo: falla «tramos positivos ≥ 3» (0/4); desarrollo: falla «supera el percentil 95 del control nulo» (-0.046 vs p95 +0.011)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `continuacion_volumen`:** 1 (esta incluida)
- **Holdout contaminado:** no
- **Pre-registro:** commit `52149b0` del 2026-11-10T06:41:47Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -155.93 R
- **Contra la madre `TREND_4H con tope de 7 días` (desarrollo):** hija -0.046 (n=2780) vs madre +0.150 (n=1784) → diferencia -0.197 [-0.350, -0.044]; peor caída -155.93 vs -65.66 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=2780 · avgR neto -0.046 [-0.087, -0.006] · bruto -0.008 · acierto 34% · duración mediana 1.0 días

Control nulo: media -0.020, p95 +0.011

**Robustez** (informativa, no decide): costos ×1.5 → -0.063 [-0.103, -0.023] · sin las 10 mejores → -0.075 [-0.111, -0.039]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-02 → 2021-06-09 | 695 | -0.024 |
| 2021-06-14 → 2022-11-08 | 695 | -0.071 |
| 2022-11-08 → 2024-03-11 | 695 | -0.039 |
| 2024-03-12 → 2025-09-08 | 695 | -0.052 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 7 | -0.236 | [-0.661, +0.189] |
| 1000FLOKIUSDT | 8 | -0.043 | [-0.728, +0.641] |
| 1000LUNCUSDT | 4 | -0.237 | [-0.724, +0.249] |
| 1000PEPEUSDT | 71 | -0.046 | [-0.295, +0.203] |
| 1000RATSUSDT | 1 | -0.622 | — |
| 1000SATSUSDT | 5 | -0.266 | [-0.707, +0.175] |
| 1000SHIBUSDT | 81 | -0.137 | [-0.325, +0.050] |
| 1MBABYDOGEUSDT | 3 | -0.679 | [-1.016, -0.342] |
| AAVEUSDT | 27 | -0.171 | [-0.459, +0.117] |
| ADAUSDT | 195 | +0.018 | [-0.150, +0.185] |
| ALGOUSDT | 6 | -0.151 | [-0.804, +0.501] |
| ALICEUSDT | 3 | -0.167 | [-0.201, -0.133] |
| APEUSDT | 19 | -0.220 | [-0.499, +0.059] |
| APTUSDT | 14 | -0.037 | [-0.571, +0.497] |
| ARBUSDT | 20 | -0.095 | [-0.351, +0.161] |
| ARKUSDT | 1 | -0.492 | — |
| ARPAUSDT | 1 | -0.925 | — |
| ATOMUSDT | 32 | +0.053 | [-0.314, +0.419] |
| AUCTIONUSDT | 1 | -0.835 | — |
| AVAXUSDT | 90 | -0.027 | [-0.214, +0.159] |
| AXSUSDT | 27 | +0.118 | [-0.469, +0.704] |
| BANDUSDT | 7 | -0.485 | [-0.765, -0.205] |
| BATUSDT | 17 | +0.096 | [-0.369, +0.560] |
| BCHUSDT | 76 | -0.109 | [-0.290, +0.073] |
| BELUSDT | 2 | +0.181 | [-1.147, +1.509] |
| BIGTIMEUSDT | 3 | -0.443 | [-0.763, -0.123] |
| BIOUSDT | 1 | +0.082 | — |
| BLZUSDT | 3 | +0.265 | [-1.694, +2.224] |
| BNBUSDT | 212 | -0.083 | [-0.219, +0.054] |
| BNTUSDT | 1 | +0.372 | — |
| BNXUSDT | 4 | +0.094 | [-1.375, +1.562] |
| BOMEUSDT | 8 | +0.061 | [-0.763, +0.886] |
| BTCUSDT | 205 | +0.062 | [-0.097, +0.221] |
| CFXUSDT | 9 | +0.063 | [-0.391, +0.517] |
| CHRUSDT | 4 | -0.450 | [-0.887, -0.014] |
| CHZUSDT | 18 | -0.065 | [-0.457, +0.326] |
| COMPUSDT | 5 | -0.163 | [-0.595, +0.269] |
| CRVUSDT | 13 | -0.215 | [-0.544, +0.113] |
| CTSIUSDT | 1 | -0.925 | — |
| DASHUSDT | 1 | -0.818 | — |
| DOGEUSDT | 92 | -0.158 | [-0.347, +0.030] |
| DOTUSDT | 51 | -0.245 | [-0.521, +0.031] |
| DYDXUSDT | 13 | +0.092 | [-0.295, +0.480] |
| EGLDUSDT | 1 | -0.986 | — |
| ENAUSDT | 23 | +0.099 | [-0.434, +0.631] |
| ENJUSDT | 1 | +1.592 | — |
| ENSUSDT | 1 | -0.685 | — |
| EOSUSDT | 52 | -0.183 | [-0.409, +0.042] |
| ETCUSDT | 43 | -0.056 | [-0.678, +0.565] |
| ETHUSDT | 133 | +0.056 | [-0.119, +0.231] |
| FARTCOINUSDT | 11 | +0.033 | [-0.623, +0.690] |
| FETUSDT | 1 | +0.800 | — |
| FILUSDT | 28 | +0.364 | [-0.329, +1.057] |
| FLMUSDT | 3 | -0.628 | [-1.260, +0.005] |
| FTMUSDT | 40 | +0.011 | [-0.263, +0.285] |
| GALAUSDT | 16 | -0.342 | [-0.665, -0.019] |
| GMTUSDT | 16 | -0.253 | [-0.831, +0.325] |
| GRTUSDT | 3 | -0.171 | [-0.324, -0.017] |
| HBARUSDT | 2 | +0.720 | [-1.546, +2.986] |
| HIGHUSDT | 1 | -0.643 | — |
| ICPUSDT | 5 | -0.247 | [-0.677, +0.183] |
| INJUSDT | 5 | -0.361 | [-0.619, -0.103] |
| IOSTUSDT | 9 | -0.551 | [-0.952, -0.150] |
| IOTXUSDT | 3 | -0.337 | [-0.820, +0.145] |
| JASMYUSDT | 1 | -0.671 | — |
| KNCUSDT | 2 | +0.306 | [+0.121, +0.492] |
| KSMUSDT | 2 | -0.705 | [-0.987, -0.423] |
| LAYERUSDT | 1 | +2.234 | — |
| LDOUSDT | 4 | -0.426 | [-0.793, -0.058] |
| LINAUSDT | 8 | +0.836 | [-0.426, +2.099] |
| LINKUSDT | 91 | -0.175 | [-0.362, +0.012] |
| LITUSDT | 3 | +0.294 | [-0.510, +1.097] |
| LRCUSDT | 1 | -0.530 | — |
| LTCUSDT | 64 | -0.092 | [-0.324, +0.139] |
| LUNAUSDT | 13 | +0.458 | [-0.310, +1.225] |
| MANAUSDT | 6 | -0.458 | [-0.769, -0.146] |
| MASKUSDT | 6 | +0.395 | [-0.616, +1.407] |
| MATICUSDT | 52 | -0.012 | [-0.314, +0.290] |
| MKRUSDT | 5 | +0.167 | [-0.626, +0.959] |
| MTLUSDT | 2 | +0.052 | [-0.100, +0.204] |
| MYXUSDT | 2 | +5.618 | [+3.678, +7.557] |
| NEARUSDT | 21 | -0.295 | [-0.616, +0.026] |
| NEIROUSDT | 7 | -0.147 | [-0.706, +0.412] |
| NEOUSDT | 17 | -0.236 | [-0.688, +0.217] |
| NMRUSDT | 1 | -0.893 | — |
| NOTUSDT | 5 | -0.508 | [-1.076, +0.061] |
| OCEANUSDT | 3 | -0.096 | [-0.858, +0.665] |
| OMGUSDT | 4 | +0.012 | [-0.808, +0.831] |
| OMUSDT | 3 | -0.778 | [-1.042, -0.513] |
| ONDOUSDT | 1 | +1.227 | — |
| ONTUSDT | 13 | -0.067 | [-0.763, +0.630] |
| OPUSDT | 24 | -0.125 | [-0.477, +0.227] |
| ORDIUSDT | 21 | -0.206 | [-0.562, +0.150] |
| PENGUUSDT | 1 | +0.739 | — |
| PEOPLEUSDT | 5 | +0.095 | [-0.703, +0.892] |
| PNUTUSDT | 12 | +0.158 | [-0.541, +0.856] |
| POPCATUSDT | 2 | -0.691 | [-1.143, -0.239] |
| PUMPUSDT | 1 | -0.682 | — |
| RAREUSDT | 3 | -0.491 | [-1.552, +0.569] |
| REEFUSDT | 7 | -0.236 | [-0.964, +0.491] |
| RNDRUSDT | 2 | -0.519 | [-0.775, -0.264] |
| RUNEUSDT | 4 | +0.410 | [-1.664, +2.484] |
| SANDUSDT | 13 | +0.306 | [-0.387, +0.999] |
| SEIUSDT | 4 | -0.275 | [-0.775, +0.226] |
| SOLUSDT | 91 | +0.051 | [-0.150, +0.253] |
| STMXUSDT | 2 | -0.287 | [-0.378, -0.196] |
| STORJUSDT | 1 | +4.695 | — |
| SUIUSDT | 32 | -0.303 | [-0.498, -0.109] |
| SUSHIUSDT | 11 | -0.380 | [-0.688, -0.072] |
| SXPUSDT | 16 | -0.355 | [-0.667, -0.042] |
| THETAUSDT | 7 | -0.345 | [-0.908, +0.217] |
| TIAUSDT | 8 | +0.185 | [-0.577, +0.947] |
| TOMOUSDT | 8 | -0.143 | [-0.545, +0.259] |
| TRBUSDT | 16 | +0.001 | [-0.460, +0.463] |
| TRUMPUSDT | 10 | -0.101 | [-0.704, +0.502] |
| TRXUSDT | 37 | -0.012 | [-0.404, +0.380] |
| TURBOUSDT | 1 | -0.279 | — |
| UMAUSDT | 1 | -0.626 | — |
| UNFIUSDT | 13 | -0.056 | [-0.636, +0.525] |
| UNIUSDT | 20 | -0.141 | [-0.456, +0.175] |
| VETUSDT | 17 | +0.378 | [-0.345, +1.101] |
| VIRTUALUSDT | 3 | +0.232 | [-0.130, +0.593] |
| VOXELUSDT | 2 | -0.334 | [-1.220, +0.551] |
| WAVESUSDT | 16 | +0.285 | [-0.508, +1.077] |
| WIFUSDT | 34 | +0.053 | [-0.264, +0.370] |
| WLDUSDT | 31 | +0.014 | [-0.323, +0.352] |
| XLMUSDT | 34 | +0.073 | [-0.794, +0.939] |
| XMRUSDT | 3 | -0.569 | [-0.820, -0.318] |
| XRPUSDT | 139 | -0.052 | [-0.226, +0.123] |
| XTZUSDT | 7 | -0.387 | [-0.821, +0.047] |
| YFIIUSDT | 1 | -0.496 | — |
| YFIUSDT | 7 | +0.037 | [-0.460, +0.533] |
| ZECUSDT | 9 | -0.176 | [-0.632, +0.280] |
| ZILUSDT | 6 | -0.285 | [-1.007, +0.436] |
| ZRXUSDT | 1 | -0.953 | — |

54 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
