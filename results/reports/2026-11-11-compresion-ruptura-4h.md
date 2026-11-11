# 2026-11-11-compresion-ruptura-4h — RECHAZADA

- **Estrategia:** `compresion_ruptura` {"bb_n": 20, "bb_k": 2.0, "ventana_pct": 180, "pct_ancho": 0.1, "vigencia": 6, "atr_n": 14, "stop_min_atr": 1.0, "trailing_atr": 2.0}
- **Universo:** futures · 4h · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-11T06:47:54+00:00 · commit `e820350`

## Hipótesis

Mecanismo: la volatilidad se agrupa; tras un período de rango muy estrecho el rango siguiente tiende a ser mayor. Mientras el precio está comprimido, quienes venden volatilidad u operan el rango dentro de la caja acumulan órdenes stop justo afuera; la ruptura las dispara y la expansión siguiente es la que paga. La dirección no se predice: se espera a que el cierre salga de la caja. Regla, UNA sola configuración fijada antes de correr: en 4h, ancho de Bollinger (20 velas, 2 σ, relativo a la media) en o por debajo del percentil 10 de los anchos de las 180 velas anteriores (30 días) = compresión; la caja es el máximo/mínimo de las 20 velas que terminan en la última vela comprimida y sigue vigente 6 velas (24 h) después; señal cuando el cierre cruza afuera de la caja (una por cruce), largo arriba, corto abajo, entrada en la apertura siguiente. Stop al otro lado de la caja, pero como mínimo a 1 ATR14 del cierre (una caja muy estrecha haría pesar la comisión de más en R). Trailing 2 ATR14 desde la entrada (lo mueve el motor); sin objetivo. Tope 42 velas (7 días): con el trailing la mediana esperada queda en 1–3 días, dentro del alcance. Comisión: 0.1% por lado (comisión + deslizamiento: se entra en una ruptura, donde el deslizamiento importa). La caja comprimida es estrecha y el ATR también se achica en la compresión, así que muchas entradas pueden quedar en el piso de 1 ATR: con un ATR de 4h de ~0.6% la comisión pesa hasta ~0.3R (y algo más si la apertura de t+1 se acerca al stop). El edge bruto tiene que superar eso; es el riesgo central y lo decide avgRNeto. Universo dinámico top 20 (sin sesgo de supervivencia). Cupo 3 por dirección como TREND_4H. La madre de control es TREND_4H con tope de 7 días: si la compresión no le gana a un Donchian común en el mismo período y tokens, no agrega nada. Criterio exigente por defecto, con el ajuste por pruebas contando las rupturas medidas en btc-signal-web (ver pruebas_previas): se acepta que eso lo hace difícil de pasar a propósito. Riesgos: evidencia D para la regla exacta, y solapa con la familia ruptura/tendencia (una ruptura de la caja suele ser también una ruptura de Donchian 20).

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 2155 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.020 [-0.010, +0.050] | ❌ |
| ajustado por 15 prueba(s) de la familia: avgR − 2.94 EE > 0 | +0.020 − 2.94×0.015 = -0.024 | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-04-01:+0.00R 2021-08-14:+0.00R 2023-01-04:-0.02R 2024-04-30:+0.09R): depende del régimen; la dispersión entre tramos (0.11R) supera el doble del avgR (0.020R) | ❌ |
| tramos positivos ≥ 3 | 3/4 | ✅ |
| supera el percentil 95 del control nulo | +0.020 vs p95 +0.008 | ✅ |
| alcance: duración mediana ≤ 7 días | 1.2 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (+0.020 [-0.010, +0.050]); desarrollo: falla «ajustado por 15 prueba(s) de la familia: avgR − 2.94 EE > 0» (+0.020 − 2.94×0.015 = -0.024); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-04-01:+0.00R 2021-08-14:+0.00R 2023-01-04:-0.02R 2024-04-30:+0.09R): depende del régimen; la dispersión entre tramos (0.11R) supera el doble del avgR (0.020R))

## Ficha

- **Nivel:** —
- **Pruebas en la familia `ruptura`:** 15 (esta incluida; 14 medidas fuera de este repo)
- **Holdout contaminado:** sí
- **Pre-registro:** commit `e820350` del 2026-11-11T06:44:46Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -29.58 R
- **Contra la madre `TREND_4H con tope de 7 días` (desarrollo):** hija +0.020 (n=2155) vs madre +0.150 (n=1784) → diferencia -0.130 [-0.281, +0.021]; peor caída -29.58 vs -65.66 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=2155 · avgR neto +0.020 [-0.010, +0.050] · bruto +0.048 · acierto 38% · duración mediana 1.2 días

Control nulo: media -0.024, p95 +0.008

**Robustez** (informativa, no decide): costos ×1.5 → +0.008 [-0.022, +0.038] · sin las 10 mejores → -0.004 [-0.030, +0.021]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-01 → 2021-08-11 | 539 | +0.004 |
| 2021-08-14 → 2023-01-04 | 539 | +0.003 |
| 2023-01-04 → 2024-04-30 | 539 | -0.018 |
| 2024-04-30 → 2025-09-08 | 538 | +0.092 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 11 | -0.153 | [-0.296, -0.010] |
| 1000FLOKIUSDT | 7 | +0.065 | [-0.318, +0.447] |
| 1000LUNCUSDT | 1 | +0.337 | — |
| 1000PEPEUSDT | 34 | +0.072 | [-0.099, +0.244] |
| 1000RATSUSDT | 4 | -0.201 | [-0.491, +0.089] |
| 1000SATSUSDT | 5 | -0.154 | [-0.325, +0.018] |
| 1000SHIBUSDT | 54 | +0.028 | [-0.143, +0.199] |
| 1MBABYDOGEUSDT | 1 | +0.104 | — |
| AAVEUSDT | 25 | +0.059 | [-0.218, +0.335] |
| ADAUSDT | 99 | -0.020 | [-0.179, +0.139] |
| ALGOUSDT | 5 | +0.044 | [-0.341, +0.429] |
| ALICEUSDT | 3 | -0.377 | [-0.540, -0.215] |
| APEUSDT | 17 | +0.231 | [-0.133, +0.595] |
| APTUSDT | 13 | -0.037 | [-0.318, +0.244] |
| ARBUSDT | 14 | -0.083 | [-0.296, +0.129] |
| ARKUSDT | 2 | +0.185 | [-0.136, +0.505] |
| ARPAUSDT | 3 | +0.029 | [-0.299, +0.358] |
| ATOMUSDT | 27 | -0.223 | [-0.333, -0.113] |
| AUCTIONUSDT | 3 | -0.312 | [-0.607, -0.017] |
| AVAXUSDT | 66 | +0.128 | [-0.062, +0.318] |
| AXSUSDT | 20 | -0.057 | [-0.298, +0.183] |
| BAKEUSDT | 3 | -0.442 | [-0.578, -0.306] |
| BANDUSDT | 8 | -0.102 | [-0.477, +0.273] |
| BATUSDT | 6 | +0.023 | [-0.743, +0.788] |
| BCHUSDT | 48 | -0.021 | [-0.177, +0.136] |
| BELUSDT | 1 | +0.292 | — |
| BIGTIMEUSDT | 1 | -0.228 | — |
| BIOUSDT | 2 | -0.091 | [-0.345, +0.163] |
| BLURUSDT | 2 | -0.174 | [-0.816, +0.469] |
| BLZUSDT | 7 | -0.131 | [-0.383, +0.121] |
| BNBUSDT | 125 | -0.039 | [-0.170, +0.091] |
| BNTUSDT | 2 | -0.424 | [-0.739, -0.110] |
| BNXUSDT | 2 | -0.202 | [-1.020, +0.615] |
| BOMEUSDT | 9 | -0.274 | [-0.472, -0.075] |
| BTCUSDT | 129 | +0.067 | [-0.059, +0.193] |
| CFXUSDT | 6 | +0.146 | [-0.223, +0.515] |
| CHRUSDT | 6 | +0.229 | [-0.361, +0.818] |
| CHZUSDT | 11 | +0.039 | [-0.324, +0.402] |
| CKBUSDT | 3 | -0.066 | [-0.545, +0.413] |
| COMPUSDT | 11 | +0.118 | [-0.300, +0.536] |
| CRVUSDT | 17 | -0.109 | [-0.297, +0.078] |
| CTSIUSDT | 3 | +0.200 | [-0.625, +1.025] |
| DASHUSDT | 5 | -0.150 | [-0.278, -0.022] |
| DOGEUSDT | 65 | +0.123 | [-0.055, +0.300] |
| DOTUSDT | 45 | +0.063 | [-0.158, +0.284] |
| DYDXUSDT | 20 | +0.069 | [-0.188, +0.326] |
| EGLDUSDT | 5 | +0.371 | [-0.579, +1.320] |
| ENAUSDT | 11 | -0.057 | [-0.271, +0.158] |
| ENJUSDT | 1 | -0.576 | — |
| EOSUSDT | 43 | +0.006 | [-0.168, +0.179] |
| ETCUSDT | 27 | +0.017 | [-0.290, +0.324] |
| ETHFIUSDT | 2 | +0.253 | [-0.208, +0.714] |
| ETHUSDT | 90 | +0.062 | [-0.103, +0.227] |
| FARTCOINUSDT | 20 | -0.026 | [-0.314, +0.261] |
| FETUSDT | 1 | +0.470 | — |
| FILUSDT | 21 | +0.180 | [-0.199, +0.558] |
| FLMUSDT | 1 | +0.552 | — |
| FRONTUSDT | 2 | +0.133 | [-0.374, +0.640] |
| FTMUSDT | 27 | -0.141 | [-0.322, +0.041] |
| FUNUSDT | 2 | -0.302 | [-1.438, +0.834] |
| GALAUSDT | 14 | +0.097 | [-0.132, +0.327] |
| GMTUSDT | 13 | -0.061 | [-0.551, +0.428] |
| GRTUSDT | 1 | -0.364 | — |
| HBARUSDT | 5 | +0.123 | [-1.010, +1.255] |
| HIGHUSDT | 2 | +1.086 | [-1.713, +3.885] |
| HNTUSDT | 2 | +0.221 | [-1.236, +1.677] |
| HYPERUSDT | 1 | -0.324 | — |
| HYPEUSDT | 1 | -0.902 | — |
| ICPUSDT | 4 | -0.339 | [-0.598, -0.080] |
| INJUSDT | 13 | -0.150 | [-0.341, +0.041] |
| IOSTUSDT | 3 | -0.170 | [-0.499, +0.160] |
| IOTXUSDT | 1 | -0.132 | — |
| JASMYUSDT | 2 | +1.463 | [+0.531, +2.394] |
| JUPUSDT | 1 | +0.453 | — |
| KAITOUSDT | 1 | +0.006 | — |
| KNCUSDT | 1 | +0.127 | — |
| KSMUSDT | 2 | +0.071 | [-0.018, +0.159] |
| LAYERUSDT | 5 | -0.007 | [-0.328, +0.315] |
| LDOUSDT | 8 | -0.038 | [-0.343, +0.268] |
| LENDUSDT | 1 | +0.934 | — |
| LINAUSDT | 9 | -0.268 | [-0.436, -0.101] |
| LINKUSDT | 65 | +0.016 | [-0.160, +0.192] |
| LITUSDT | 1 | -0.470 | — |
| LPTUSDT | 3 | -0.107 | [-0.496, +0.282] |
| LQTYUSDT | 1 | -0.480 | — |
| LRCUSDT | 3 | +0.243 | [-0.699, +1.184] |
| LTCUSDT | 54 | -0.067 | [-0.231, +0.098] |
| LUNAUSDT | 15 | +0.296 | [-0.041, +0.634] |
| MANAUSDT | 7 | +0.068 | [-0.313, +0.448] |
| MASKUSDT | 11 | +0.309 | [+0.017, +0.602] |
| MATICUSDT | 35 | +0.018 | [-0.166, +0.203] |
| MEWUSDT | 3 | -0.191 | [-0.327, -0.055] |
| MKRUSDT | 9 | -0.143 | [-0.671, +0.385] |
| MOODENGUSDT | 2 | +0.054 | [-0.865, +0.974] |
| MTLUSDT | 4 | +0.262 | [+0.005, +0.519] |
| NEARUSDT | 20 | -0.157 | [-0.325, +0.010] |
| NEIROUSDT | 8 | +0.405 | [-0.456, +1.266] |
| NEOUSDT | 15 | -0.241 | [-0.417, -0.066] |
| NMRUSDT | 3 | -0.553 | [-0.668, -0.437] |
| NOTUSDT | 4 | +0.002 | [-0.313, +0.316] |
| OMGUSDT | 2 | -0.341 | [-0.507, -0.175] |
| OMUSDT | 1 | -0.275 | — |
| ONDOUSDT | 2 | +0.288 | [-0.091, +0.667] |
| ONEUSDT | 1 | -0.050 | — |
| ONGUSDT | 4 | -0.007 | [-0.297, +0.284] |
| ONTUSDT | 8 | -0.020 | [-0.286, +0.245] |
| OPUSDT | 19 | +0.161 | [-0.101, +0.423] |
| ORDIUSDT | 10 | +0.422 | [-0.119, +0.963] |
| PENGUUSDT | 1 | -0.479 | — |
| PEOPLEUSDT | 9 | +0.000 | [-0.385, +0.386] |
| PERPUSDT | 3 | +0.116 | [-0.468, +0.700] |
| PNUTUSDT | 11 | +0.233 | [-0.286, +0.752] |
| POPCATUSDT | 3 | +0.056 | [-0.469, +0.581] |
| PUMPUSDT | 5 | +0.098 | [-0.333, +0.529] |
| RAREUSDT | 1 | +0.127 | — |
| REEFUSDT | 8 | +0.104 | [-0.280, +0.489] |
| RNDRUSDT | 3 | +0.807 | [-1.449, +3.063] |
| RSRUSDT | 3 | -0.210 | [-0.826, +0.406] |
| RUNEUSDT | 9 | +0.087 | [-0.443, +0.616] |
| RVNUSDT | 3 | -0.406 | [-0.448, -0.363] |
| SANDUSDT | 12 | -0.108 | [-0.525, +0.309] |
| SEIUSDT | 6 | -0.003 | [-0.352, +0.345] |
| SOLUSDT | 70 | +0.037 | [-0.118, +0.192] |
| STMXUSDT | 6 | -0.172 | [-0.344, +0.001] |
| STORJUSDT | 11 | +0.459 | [-0.956, +1.874] |
| STXUSDT | 4 | -0.189 | [-0.363, -0.015] |
| SUIUSDT | 28 | +0.225 | [-0.415, +0.865] |
| SUSHIUSDT | 20 | -0.113 | [-0.260, +0.033] |
| SXPUSDT | 14 | -0.035 | [-0.297, +0.226] |
| THETAUSDT | 15 | -0.129 | [-0.302, +0.045] |
| TIAUSDT | 15 | +0.055 | [-0.246, +0.355] |
| TOMOUSDT | 6 | +0.062 | [-0.477, +0.601] |
| TONUSDT | 2 | -0.404 | [-0.556, -0.252] |
| TRBUSDT | 11 | +0.171 | [-0.357, +0.699] |
| TRUMPUSDT | 9 | +0.138 | [-0.275, +0.552] |
| TRXUSDT | 29 | -0.052 | [-0.205, +0.101] |
| TURBOUSDT | 3 | -0.181 | [-0.791, +0.430] |
| UMAUSDT | 4 | -0.345 | [-0.621, -0.069] |
| UNFIUSDT | 2 | -0.463 | [-0.574, -0.352] |
| UNIUSDT | 15 | -0.051 | [-0.318, +0.216] |
| UXLINKUSDT | 2 | +0.208 | [-0.470, +0.887] |
| VETUSDT | 11 | -0.066 | [-0.313, +0.181] |
| VIRTUALUSDT | 2 | -0.195 | [-0.502, +0.112] |
| VOXELUSDT | 4 | +0.213 | [-0.322, +0.748] |
| WAVESUSDT | 16 | -0.074 | [-0.310, +0.161] |
| WIFUSDT | 24 | +0.092 | [-0.151, +0.335] |
| WLDUSDT | 22 | -0.051 | [-0.324, +0.222] |
| XLMUSDT | 27 | +0.308 | [-0.192, +0.808] |
| XMRUSDT | 4 | -0.155 | [-0.568, +0.258] |
| XRPUSDT | 65 | +0.012 | [-0.201, +0.225] |
| XTZUSDT | 10 | -0.098 | [-0.396, +0.200] |
| YFIIUSDT | 2 | -0.469 | [-0.649, -0.288] |
| YFIUSDT | 8 | +0.007 | [-0.429, +0.442] |
| ZECUSDT | 5 | +0.162 | [-0.642, +0.967] |
| ZILUSDT | 6 | -0.294 | [-0.486, -0.102] |
| ZRXUSDT | 2 | +0.385 | [-0.831, +1.601] |

33 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
