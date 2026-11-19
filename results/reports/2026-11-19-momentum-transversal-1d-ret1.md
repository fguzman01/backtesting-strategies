# 2026-11-19-momentum-transversal-1d-ret1 — RECHAZADA

- **Estrategia:** `momentum_transversal` {"lookback": 1, "k": 3, "atr_n": 14, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 1d · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-19T06:45:13+00:00 · commit `2b7dafb`

## Hipótesis

Mecanismo: en las monedas más líquidas el retorno del día anterior continúa al siguiente porque los flujos y la atención llegan escalonados; la reversión es propia de las ilíquidas, y el universo dinámico top 20 son justamente las más operadas de cada mes. Quien pierde es el que vende a destiempo contra el flujo del día (o compra la caída ya agotada). Regla, UNA sola configuración fijada antes de correr y tomada de la fuente, no de datos: cada vela diaria `t`, entre los símbolos vigentes del top 20 del mes se rankea el retorno de 1 cierre (cierre_t / cierre_{t-1} − 1); largo los 3 mejores, corto los 3 peores (sólo si hay al menos 6 vigentes). Sentido: momentum, fijado antes de correr; la reversión de 1 día (el signo dominante del resto del universo según la misma literatura) NO se prueba aparte, y tampoco los horizontes de 2 o 3 días. Entrada en la apertura de la vela siguiente. Stop a 2 ATR(14) desde la entrada y trailing a 2 ATR desde el mejor precio desde la entrada (lo mueve el motor); sin objetivo; tope 5 velas diarias. Costos: 0.1% por lado (0.05% comisión + 0.05% deslizamiento) y funding de futuros; con stop de 2 ATR diario (~5–7% en cripto líquida) la comisión pesa ~0.03–0.04R por operación.
Riesgos declarados: (1) es la mitad de la idea #17 que quedó sin medir y su madre se rechazó con 7 días (−0.012): si el retorno de 1 día tampoco paga, la familia queda cerrada; (2) la rotación diaria y la comisión se comen un efecto de un día (Han, Kang & Ryu); un retorno de 1 día es también la señal más expuesta a la reversión por rebote del día siguiente; (3) las señales de 3+3 símbolos del mismo mercado no son independientes, el IC de ±2 EE es optimista y el control nulo y los tramos son el contrapeso; (4) la dirección neta no está neutralizada por beta; (5) el holdout se declara contaminado (ver `holdout_contaminado`). Criterio exigente por defecto, sin aflojar nada.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 3023 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | -0.022 [-0.053, +0.009] | ❌ |
| ajustado por 3 prueba(s) de la familia: avgR − 2.39 EE > 0 | -0.022 − 2.39×0.015 = -0.059 | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-04-02:-0.02R 2021-08-02:-0.03R 2022-12-22:-0.07R 2024-04-28:+0.03R): depende del régimen; la dispersión entre tramos (0.10R) supera el doble del avgR (-0.022R) | ❌ |
| tramos positivos ≥ 3 | 1/4 | ❌ |
| supera el percentil 95 del control nulo | -0.022 vs p95 +0.026 | ❌ |
| alcance: duración mediana ≤ 14 días | 5.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (-0.022 [-0.053, +0.009]); desarrollo: falla «ajustado por 3 prueba(s) de la familia: avgR − 2.39 EE > 0» (-0.022 − 2.39×0.015 = -0.059); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-04-02:-0.02R 2021-08-02:-0.03R 2022-12-22:-0.07R 2024-04-28:+0.03R): depende del régimen; la dispersión entre tramos (0.10R) supera el doble del avgR (-0.022R)); desarrollo: falla «tramos positivos ≥ 3» (1/4); desarrollo: falla «supera el percentil 95 del control nulo» (-0.022 vs p95 +0.026)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `corte_transversal`:** 3 (esta incluida; 1 medidas fuera de este repo)
  - `2026-11-18-momentum-transversal-1d`: RECHAZADA, desarrollo -0.012
- **Holdout contaminado:** sí
- **Pre-registro:** commit `2b7dafb` del 2026-11-19T06:41:42Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -99.73 R
- **Contra la madre `momentum transversal 7 días (2026-11-18)` (desarrollo):** hija -0.022 (n=3023) vs madre -0.012 (n=2857) → diferencia -0.010 [-0.056, +0.035]; peor caída -99.73 vs -72.09 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=3023 · avgR neto -0.022 [-0.053, +0.009] · bruto -0.008 · acierto 45% · duración mediana 5.0 días

Control nulo: media -0.006, p95 +0.026

**Robustez** (informativa, no decide): costos ×1.5 → -0.028 [-0.059, +0.003] · sin las 10 mejores → -0.043 [-0.066, -0.020]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-02 → 2021-08-02 | 756 | -0.017 |
| 2021-08-02 → 2022-12-22 | 756 | -0.027 |
| 2022-12-22 → 2024-04-28 | 756 | -0.071 |
| 2024-04-28 → 2025-09-08 | 755 | +0.026 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 15 | -0.106 | [-0.351, +0.139] |
| 1000FLOKIUSDT | 5 | -0.360 | [-0.855, +0.136] |
| 1000LUNCUSDT | 1 | -0.104 | — |
| 1000PEPEUSDT | 77 | -0.010 | [-0.167, +0.148] |
| 1000RATSUSDT | 6 | -0.262 | [-0.747, +0.224] |
| 1000SATSUSDT | 10 | -0.045 | [-0.428, +0.339] |
| 1000SHIBUSDT | 57 | -0.241 | [-0.362, -0.120] |
| 1MBABYDOGEUSDT | 1 | +0.830 | — |
| AAVEUSDT | 38 | +0.066 | [-0.163, +0.295] |
| ADAUSDT | 132 | +0.104 | [-0.038, +0.246] |
| ALGOUSDT | 8 | +0.010 | [-0.309, +0.329] |
| ALICEUSDT | 9 | -0.117 | [-0.404, +0.170] |
| ALPACAUSDT | 5 | -0.039 | [-0.082, +0.003] |
| APEUSDT | 21 | -0.120 | [-0.344, +0.104] |
| APTUSDT | 17 | -0.082 | [-0.346, +0.183] |
| ARBUSDT | 21 | -0.105 | [-0.345, +0.135] |
| ARKUSDT | 2 | -0.014 | [-0.076, +0.048] |
| ARPAUSDT | 4 | -0.030 | [-0.426, +0.366] |
| ATOMUSDT | 53 | -0.034 | [-0.227, +0.158] |
| AUCTIONUSDT | 5 | +0.048 | [-0.057, +0.153] |
| AVAXUSDT | 88 | +0.067 | [-0.084, +0.218] |
| AXSUSDT | 24 | +0.013 | [-0.205, +0.232] |
| BAKEUSDT | 6 | -0.120 | [-0.469, +0.229] |
| BANDUSDT | 12 | -0.093 | [-0.359, +0.172] |
| BATUSDT | 9 | +0.132 | [-0.159, +0.422] |
| BCHUSDT | 74 | -0.045 | [-0.193, +0.103] |
| BELUSDT | 3 | -0.297 | [-0.953, +0.359] |
| BIGTIMEUSDT | 4 | -0.293 | [-0.798, +0.212] |
| BIOUSDT | 2 | -0.323 | [-1.201, +0.554] |
| BLURUSDT | 3 | +0.257 | [-0.054, +0.569] |
| BLZUSDT | 9 | +0.336 | [-0.475, +1.147] |
| BNBUSDT | 184 | -0.002 | [-0.112, +0.109] |
| BNTUSDT | 4 | +1.188 | [-1.732, +4.108] |
| BNXUSDT | 8 | +0.156 | [-0.281, +0.593] |
| BOMEUSDT | 15 | -0.315 | [-0.600, -0.029] |
| BTCUSDT | 174 | +0.092 | [-0.011, +0.195] |
| CFXUSDT | 12 | +0.205 | [-0.171, +0.580] |
| CHRUSDT | 10 | -0.067 | [-0.357, +0.223] |
| CHZUSDT | 32 | -0.044 | [-0.240, +0.152] |
| CKBUSDT | 5 | -0.527 | [-1.056, +0.002] |
| COMPUSDT | 11 | -0.061 | [-0.318, +0.197] |
| CRVUSDT | 19 | +0.081 | [-0.231, +0.392] |
| CTSIUSDT | 5 | -0.190 | [-0.695, +0.316] |
| DASHUSDT | 3 | +0.239 | [-0.192, +0.669] |
| DOGEUSDT | 92 | -0.032 | [-0.169, +0.105] |
| DOTUSDT | 49 | +0.037 | [-0.166, +0.241] |
| DYDXUSDT | 26 | -0.062 | [-0.291, +0.167] |
| EGLDUSDT | 4 | -0.032 | [-0.569, +0.504] |
| ENAUSDT | 38 | +0.018 | [-0.200, +0.237] |
| ENJUSDT | 3 | -0.113 | [-1.005, +0.778] |
| ENSUSDT | 1 | -0.104 | — |
| EOSUSDT | 45 | -0.199 | [-0.329, -0.070] |
| ETCUSDT | 44 | -0.099 | [-0.279, +0.082] |
| ETHFIUSDT | 2 | +0.402 | [-1.407, +2.211] |
| ETHUSDT | 112 | -0.050 | [-0.175, +0.075] |
| FARTCOINUSDT | 28 | -0.019 | [-0.269, +0.230] |
| FETUSDT | 3 | +0.054 | [-0.169, +0.277] |
| FILUSDT | 36 | +0.142 | [-0.092, +0.376] |
| FLMUSDT | 3 | -0.098 | [-1.188, +0.992] |
| FRONTUSDT | 1 | -0.200 | — |
| FTMUSDT | 59 | -0.052 | [-0.221, +0.117] |
| FTTUSDT | 3 | -0.013 | [-0.025, -0.002] |
| FUNUSDT | 2 | +0.898 | [+0.166, +1.631] |
| GALAUSDT | 24 | -0.289 | [-0.505, -0.074] |
| GMTUSDT | 28 | -0.059 | [-0.242, +0.124] |
| GRTUSDT | 7 | -0.046 | [-0.404, +0.313] |
| HBARUSDT | 5 | +0.272 | [-0.314, +0.857] |
| HIGHUSDT | 3 | -0.535 | [-1.032, -0.037] |
| HNTUSDT | 1 | +0.198 | — |
| HYPERUSDT | 1 | +0.069 | — |
| ICPUSDT | 5 | -0.622 | [-0.997, -0.247] |
| INJUSDT | 13 | -0.062 | [-0.405, +0.280] |
| IOSTUSDT | 9 | -0.406 | [-0.816, +0.004] |
| IOTXUSDT | 3 | -0.774 | [-0.915, -0.633] |
| JASMYUSDT | 2 | +0.093 | [-0.632, +0.817] |
| JUPUSDT | 3 | -0.121 | [-0.739, +0.496] |
| KNCUSDT | 4 | +0.276 | [-0.475, +1.026] |
| KSMUSDT | 2 | -0.040 | [-0.799, +0.718] |
| LAYERUSDT | 3 | +0.267 | [-0.576, +1.109] |
| LDOUSDT | 5 | -0.280 | [-0.661, +0.102] |
| LENDUSDT | 4 | -0.110 | [-0.307, +0.086] |
| LINAUSDT | 9 | -0.008 | [-0.308, +0.292] |
| LINKUSDT | 111 | -0.146 | [-0.264, -0.028] |
| LITUSDT | 5 | +0.550 | [+0.088, +1.012] |
| LPTUSDT | 2 | -0.121 | [-0.354, +0.113] |
| LQTYUSDT | 2 | +0.274 | [+0.003, +0.546] |
| LRCUSDT | 1 | +0.024 | — |
| LTCUSDT | 63 | -0.062 | [-0.214, +0.090] |
| LUNAUSDT | 19 | +0.015 | [-0.281, +0.311] |
| MANAUSDT | 8 | -0.148 | [-0.473, +0.177] |
| MASKUSDT | 14 | -0.063 | [-0.312, +0.185] |
| MATICUSDT | 49 | -0.089 | [-0.290, +0.112] |
| MEWUSDT | 2 | -0.353 | [-1.465, +0.759] |
| MKRUSDT | 10 | -0.028 | [-0.392, +0.336] |
| MOODENGUSDT | 2 | +0.256 | [-0.460, +0.972] |
| MTLUSDT | 5 | +0.311 | [-0.257, +0.878] |
| MYXUSDT | 2 | +14.326 | [-15.424, +44.077] |
| NEARUSDT | 38 | +0.028 | [-0.198, +0.255] |
| NEIROUSDT | 8 | +0.090 | [-0.335, +0.514] |
| NEOUSDT | 16 | +0.013 | [-0.228, +0.254] |
| NMRUSDT | 1 | -0.327 | — |
| NOTUSDT | 8 | +0.321 | [-0.021, +0.662] |
| OCEANUSDT | 1 | +0.340 | — |
| OMGUSDT | 7 | -0.634 | [-0.911, -0.356] |
| OMUSDT | 5 | +0.017 | [-0.242, +0.277] |
| ONDOUSDT | 3 | -0.002 | [-0.159, +0.155] |
| ONEUSDT | 1 | -0.782 | — |
| ONGUSDT | 4 | +0.135 | [-0.205, +0.475] |
| ONTUSDT | 15 | -0.192 | [-0.414, +0.030] |
| OPUSDT | 24 | +0.036 | [-0.239, +0.311] |
| ORDIUSDT | 25 | +0.046 | [-0.202, +0.295] |
| PENGUUSDT | 1 | +0.207 | — |
| PEOPLEUSDT | 11 | +0.129 | [-0.299, +0.557] |
| PERPUSDT | 3 | -0.101 | [-0.211, +0.008] |
| PNUTUSDT | 6 | -0.050 | [-0.547, +0.448] |
| POPCATUSDT | 4 | +0.063 | [-0.444, +0.570] |
| PUMPUSDT | 2 | +0.100 | [-0.701, +0.900] |
| RAREUSDT | 3 | -0.182 | [-0.522, +0.158] |
| REEFUSDT | 10 | +0.023 | [-0.423, +0.469] |
| RNDRUSDT | 3 | -0.297 | [-1.340, +0.747] |
| RSRUSDT | 3 | -0.032 | [-0.185, +0.121] |
| RUNEUSDT | 8 | +0.542 | [-0.132, +1.215] |
| RVNUSDT | 2 | -0.071 | [-0.352, +0.211] |
| SANDUSDT | 20 | -0.093 | [-0.358, +0.172] |
| SEIUSDT | 8 | +0.152 | [-0.144, +0.447] |
| SOLUSDT | 89 | +0.031 | [-0.140, +0.202] |
| STMXUSDT | 4 | -0.511 | [-0.934, -0.088] |
| STORJUSDT | 10 | -0.130 | [-0.438, +0.178] |
| STXUSDT | 2 | -0.208 | [-1.396, +0.980] |
| SUIUSDT | 40 | -0.009 | [-0.275, +0.257] |
| SUSHIUSDT | 21 | -0.201 | [-0.428, +0.026] |
| SXPUSDT | 19 | +0.086 | [-0.134, +0.306] |
| THETAUSDT | 12 | -0.109 | [-0.414, +0.196] |
| TIAUSDT | 14 | -0.206 | [-0.641, +0.230] |
| TOMOUSDT | 6 | -0.386 | [-0.882, +0.111] |
| TONUSDT | 1 | -0.408 | — |
| TRBUSDT | 19 | -0.133 | [-0.361, +0.094] |
| TRUMPUSDT | 6 | -0.005 | [-0.382, +0.372] |
| TRXUSDT | 33 | -0.111 | [-0.303, +0.081] |
| TURBOUSDT | 3 | -0.467 | [-0.754, -0.180] |
| UMAUSDT | 2 | -0.240 | [-0.593, +0.113] |
| UNFIUSDT | 10 | -0.306 | [-0.615, +0.003] |
| UNIUSDT | 19 | -0.214 | [-0.460, +0.032] |
| UXLINKUSDT | 3 | +0.042 | [-0.433, +0.517] |
| VETUSDT | 20 | -0.163 | [-0.603, +0.277] |
| VIRTUALUSDT | 3 | -0.247 | [-0.592, +0.097] |
| VOXELUSDT | 1 | -0.350 | — |
| WAVESUSDT | 21 | +0.054 | [-0.264, +0.372] |
| WIFUSDT | 32 | +0.106 | [-0.094, +0.305] |
| WLDUSDT | 33 | -0.198 | [-0.398, +0.001] |
| XLMUSDT | 30 | -0.063 | [-0.300, +0.175] |
| XMRUSDT | 5 | +0.044 | [-0.327, +0.415] |
| XRPUSDT | 106 | -0.041 | [-0.208, +0.127] |
| XTZUSDT | 12 | -0.129 | [-0.548, +0.290] |
| YFIIUSDT | 2 | +0.122 | [-0.630, +0.875] |
| YFIUSDT | 6 | -0.174 | [-0.334, -0.013] |
| ZECUSDT | 11 | -0.412 | [-0.783, -0.040] |
| ZILUSDT | 5 | -0.127 | [-0.580, +0.325] |
| ZRXUSDT | 3 | -0.037 | [-0.660, +0.587] |

30 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
