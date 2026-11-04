# 2026-11-04-trend4h-t7-universo-dinamico — OBSERVACION

- **Estrategia:** `tendencia_donchian` {"entrada": 20, "salida": 10, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 4h · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-04T19:31:14+00:00 · commit `2c95994+cambios`

## Hipótesis

Pregunta de medición, no una estrategia nueva (backlog B-05): cuánto del edge de `2026-11-02-trend4h-tope-7d` (TREND_4H_T7, en paper en btc-signal-web) es sesgo de supervivencia. Se aprobó (hoy en observación) midiendo sólo los 14 tokens que siguen vivos. Este par de specs corre la MISMA regla, parámetros, costos y tope en la MISMA ventana (desde 2020-04, primer mes de la tabla del universo, sin historia de spot): `una con el universo de cada spec; control: los 14 tokens fijos (2026-11-04-trend4h-t7-control-14)`. La diferencia entre los dos avgR de desarrollo es lo que aportaba elegir sobrevivientes. Sin cupo, igual que la evaluación original, para cambiar una sola cosa. Criterio exigente por defecto (como toda spec nueva); el veredicto de cada una importa menos que la comparación. Holdout contaminado: ya se miró al aprobarla. Esta es la del universo dinámico: los 20 perpetuos cripto más operados de cada mes, incluidos los retirados.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 5639 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.126 [+0.062, +0.191] | ✅ |
| avgR neto > 0 | +0.126 | ✅ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 4/4 | ✅ |
| supera el percentil 95 del control nulo | +0.126 vs p95 +0.019 | ✅ |
| alcance: duración mediana ≤ 7 días | 3.0 días | ✅ |
| holdout: hay operaciones | n=1256 | ✅ |
| holdout: avgR neto > 0 | +0.027 (n=1256) | ✅ |
| holdout: con costos ×1.5 avgR > 0 | +0.005 | ✅ |
| holdout: sin las 10 mejores avgR ≥ 0 | -0.085 | ❌ |
| holdout: conserva ≥ 33% del avgR de desarrollo | +0.027 vs mínimo +0.042 | ❌ |

**Motivos:** holdout: sin las 10 mejores avgR ≥ 0 (-0.085); holdout: conserva ≥ 33% del avgR de desarrollo (+0.027 vs mínimo +0.042); holdout contaminado: ese período ya se miró con una estrategia emparentada

## Ficha

- **Nivel:** observacion
- **Pruebas en la familia `tendencia`:** 10 (esta incluida; 4 medidas fuera de este repo)
  - `2026-10-31-trend1d-tope-7d`: RECHAZADA, desarrollo +0.087
  - `2026-11-01-trend1d-chandelier-14d`: RECHAZADA, desarrollo +0.148
  - `2026-11-02-trend4h-tope-7d`: APROBADA, desarrollo +0.245, holdout mirado
  - `2026-11-04-trend1d-trailing-atr-real-14d`: RECHAZADA, desarrollo +0.049
  - `2026-11-04-trend4h-t7-control-14`: OBSERVACION, desarrollo +0.189, holdout mirado
- **Holdout contaminado:** sí
- **Pre-registro:** commit `83f0bc7` del 2026-11-04T18:51:09Z
- **Cupo de cartera:** sin cupo
- **Peor caída (desarrollo):** -97.30 R
- **Peor caída (holdout):** -127.28 R
- **En la cartera de lo aprobado** (2020-04 → 2026-10): peor caída -236.3 R → -356.7 R; correlación mensual: `2026-11-02-trend4h-tope-7d` +0.73, `2026-11-04-trend4h-t7-control-14` +0.84

## Estabilidad de parámetros

Misma spec en desarrollo con todos los parámetros numéricos movidos a la vez. Si sólo funciona con los números exactos, es sobreajuste.

| Parámetros | n | avgR neto | ±2 EE | Conserva |
|---|---|---|---|---|
| como se pre-registraron | 5639 | +0.126 | [+0.062, +0.191] | 100% |
| ×0.8 {"entrada": 16, "salida": 8, "atr_n": 16, "ema_n": 160, "stop_atr": 1.6} | 6808 | +0.104 | [+0.041, +0.167] | 82% |
| ×1.2 {"entrada": 24, "salida": 12, "atr_n": 24, "ema_n": 240, "stop_atr": 2.4} | 4851 | +0.109 | [+0.048, +0.170] | 87% |

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=5639 · avgR neto +0.126 [+0.062, +0.191] · bruto +0.180 · acierto 33% · duración mediana 3.0 días

Control nulo: media -0.031, p95 +0.019

**Robustez** (informativa, no decide): costos ×1.5 → +0.108 [+0.043, +0.172] · sin las 10 mejores → +0.073 [+0.026, +0.120]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-06 → 2021-08-21 | 1410 | +0.226 |
| 2021-08-21 → 2023-01-14 | 1410 | +0.113 |
| 2023-01-14 → 2024-05-27 | 1410 | +0.047 |
| 2024-05-27 → 2025-09-08 | 1409 | +0.119 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 15 | -0.240 | [-0.711, +0.232] |
| 1000FLOKIUSDT | 15 | +0.028 | [-0.752, +0.807] |
| 1000LUNCUSDT | 3 | +0.031 | [-2.072, +2.133] |
| 1000PEPEUSDT | 104 | +0.131 | [-0.274, +0.535] |
| 1000RATSUSDT | 5 | +0.130 | [-1.052, +1.312] |
| 1000SATSUSDT | 14 | -0.139 | [-0.760, +0.482] |
| 1000SHIBUSDT | 106 | -0.173 | [-0.441, +0.095] |
| 1MBABYDOGEUSDT | 4 | +0.296 | [-1.141, +1.732] |
| AAVEUSDT | 53 | +0.085 | [-0.268, +0.438] |
| ADAUSDT | 243 | +0.216 | [-0.081, +0.513] |
| ALGOUSDT | 8 | +0.072 | [-0.695, +0.840] |
| ALICEUSDT | 9 | +0.075 | [-1.353, +1.503] |
| APEUSDT | 30 | +0.528 | [-0.158, +1.213] |
| APTUSDT | 30 | -0.232 | [-0.639, +0.176] |
| ARBUSDT | 33 | -0.026 | [-0.527, +0.476] |
| ARKUSDT | 4 | -0.519 | [-1.121, +0.083] |
| ARPAUSDT | 5 | -0.399 | [-1.174, +0.377] |
| ATOMUSDT | 70 | -0.089 | [-0.481, +0.303] |
| AUCTIONUSDT | 3 | -0.162 | [-1.101, +0.777] |
| AVAXUSDT | 164 | +0.062 | [-0.177, +0.301] |
| AXSUSDT | 41 | +0.183 | [-0.439, +0.806] |
| BAKEUSDT | 4 | +0.280 | [-0.997, +1.557] |
| BANDUSDT | 16 | -0.430 | [-0.975, +0.114] |
| BATUSDT | 11 | -0.134 | [-1.436, +1.168] |
| BCHUSDT | 112 | +0.148 | [-0.207, +0.502] |
| BELUSDT | 4 | -0.293 | [-1.167, +0.582] |
| BIGTIMEUSDT | 4 | -0.241 | [-1.253, +0.771] |
| BIOUSDT | 2 | -0.629 | [-1.522, +0.264] |
| BLURUSDT | 4 | -0.715 | [-1.340, -0.090] |
| BLZUSDT | 10 | +1.122 | [-0.568, +2.812] |
| BNBUSDT | 280 | +0.193 | [-0.081, +0.467] |
| BNTUSDT | 3 | +6.355 | [-7.962, +20.672] |
| BNXUSDT | 8 | +0.651 | [-1.065, +2.367] |
| BOMEUSDT | 26 | -0.262 | [-0.653, +0.128] |
| BTCUSDT | 279 | +0.190 | [-0.094, +0.473] |
| CFXUSDT | 12 | +0.138 | [-0.558, +0.833] |
| CHRUSDT | 12 | -0.454 | [-1.039, +0.131] |
| CHZUSDT | 39 | -0.252 | [-0.634, +0.130] |
| CKBUSDT | 4 | -0.493 | [-1.192, +0.205] |
| COMPUSDT | 12 | +0.260 | [-0.397, +0.918] |
| CRVUSDT | 21 | +0.211 | [-0.330, +0.752] |
| CTSIUSDT | 5 | +0.006 | [-1.341, +1.354] |
| DASHUSDT | 9 | -0.487 | [-0.962, -0.011] |
| DOGEUSDT | 207 | +0.228 | [-0.181, +0.637] |
| DOTUSDT | 103 | +0.202 | [-0.138, +0.542] |
| DYDXUSDT | 33 | +0.003 | [-0.570, +0.577] |
| EGLDUSDT | 3 | +1.801 | [-3.584, +7.186] |
| ENAUSDT | 46 | +0.139 | [-0.332, +0.609] |
| ENJUSDT | 4 | +0.254 | [-0.726, +1.235] |
| ENSUSDT | 3 | +0.049 | [-1.789, +1.888] |
| EOSUSDT | 109 | +0.064 | [-0.266, +0.394] |
| ETCUSDT | 100 | +0.318 | [-0.251, +0.887] |
| ETHFIUSDT | 5 | +0.888 | [-1.925, +3.701] |
| ETHUSDT | 288 | +0.217 | [-0.031, +0.466] |
| FARTCOINUSDT | 31 | -0.254 | [-0.610, +0.103] |
| FETUSDT | 8 | -0.799 | [-1.026, -0.573] |
| FILUSDT | 66 | +0.303 | [-0.295, +0.901] |
| FLMUSDT | 6 | +0.087 | [-1.132, +1.306] |
| FRONTUSDT | 4 | -0.473 | [-1.206, +0.259] |
| FTMUSDT | 83 | +0.160 | [-0.157, +0.477] |
| FUNUSDT | 6 | +0.100 | [-0.948, +1.147] |
| GALAUSDT | 38 | +0.435 | [-0.201, +1.072] |
| GMTUSDT | 42 | +0.021 | [-0.396, +0.437] |
| GRTUSDT | 11 | -0.220 | [-0.841, +0.400] |
| HBARUSDT | 10 | -0.274 | [-1.015, +0.467] |
| HIGHUSDT | 4 | +1.308 | [-0.314, +2.931] |
| HNTUSDT | 3 | +0.740 | [-0.280, +1.760] |
| HYPERUSDT | 6 | -0.852 | [-1.094, -0.610] |
| HYPEUSDT | 1 | +2.027 | — |
| ICPUSDT | 8 | +0.612 | [-0.821, +2.045] |
| INJUSDT | 26 | +0.128 | [-0.444, +0.701] |
| IOSTUSDT | 13 | -0.742 | [-1.040, -0.444] |
| IOTXUSDT | 4 | +0.395 | [-0.149, +0.940] |
| JASMYUSDT | 4 | +0.673 | [-0.278, +1.624] |
| JUPUSDT | 5 | -0.340 | [-0.855, +0.175] |
| KAITOUSDT | 5 | -0.310 | [-0.956, +0.337] |
| KLAYUSDT | 5 | -0.561 | [-1.101, -0.022] |
| KNCUSDT | 7 | +1.003 | [-0.203, +2.209] |
| KSMUSDT | 2 | -0.362 | [-1.171, +0.447] |
| LAYERUSDT | 4 | +0.576 | [-0.862, +2.014] |
| LDOUSDT | 17 | -0.234 | [-0.740, +0.271] |
| LENDUSDT | 2 | -0.317 | [-1.724, +1.090] |
| LINAUSDT | 16 | +0.009 | [-1.344, +1.361] |
| LINKUSDT | 215 | +0.144 | [-0.122, +0.410] |
| LITUSDT | 4 | +0.796 | [-0.258, +1.851] |
| LPTUSDT | 3 | +0.160 | [-0.199, +0.519] |
| LQTYUSDT | 5 | -0.553 | [-0.999, -0.107] |
| LRCUSDT | 6 | -0.681 | [-1.096, -0.265] |
| LTCUSDT | 172 | +0.080 | [-0.202, +0.362] |
| LUNAUSDT | 35 | +0.512 | [-0.418, +1.443] |
| MANAUSDT | 22 | -0.020 | [-0.494, +0.454] |
| MASKUSDT | 27 | -0.157 | [-0.501, +0.187] |
| MATICUSDT | 122 | +0.110 | [-0.204, +0.425] |
| MEWUSDT | 4 | -0.667 | [-1.148, -0.185] |
| MKRUSDT | 12 | +0.028 | [-1.097, +1.152] |
| MOODENGUSDT | 7 | -0.574 | [-1.104, -0.044] |
| MTLUSDT | 7 | +0.123 | [-0.861, +1.107] |
| MYXUSDT | 2 | +53.085 | [-55.047, +161.217] |
| NEARUSDT | 59 | +0.113 | [-0.232, +0.459] |
| NEIROUSDT | 18 | +0.336 | [-0.530, +1.201] |
| NEOUSDT | 34 | -0.128 | [-0.627, +0.370] |
| NMRUSDT | 6 | -0.081 | [-1.844, +1.682] |
| NOTUSDT | 15 | -0.257 | [-0.832, +0.318] |
| OCEANUSDT | 3 | +3.016 | [-0.812, +6.844] |
| OMGUSDT | 9 | -0.309 | [-0.824, +0.206] |
| OMUSDT | 3 | -0.602 | [-1.413, +0.209] |
| ONDOUSDT | 7 | -0.316 | [-0.914, +0.282] |
| ONEUSDT | 3 | +0.478 | [-1.466, +2.421] |
| ONGUSDT | 6 | -0.267 | [-1.056, +0.522] |
| ONTUSDT | 22 | -0.335 | [-0.804, +0.133] |
| OPUSDT | 51 | +0.024 | [-0.365, +0.413] |
| ORDIUSDT | 46 | +0.096 | [-0.290, +0.482] |
| PENGUUSDT | 6 | -0.350 | [-1.157, +0.457] |
| PEOPLEUSDT | 25 | -0.153 | [-0.746, +0.439] |
| PERPUSDT | 6 | -0.268 | [-1.007, +0.471] |
| PNUTUSDT | 20 | -0.422 | [-0.790, -0.055] |
| POPCATUSDT | 5 | -0.454 | [-1.105, +0.197] |
| PUMPUSDT | 4 | -0.583 | [-1.044, -0.123] |
| RAREUSDT | 3 | -0.592 | [-1.460, +0.276] |
| REEFUSDT | 12 | -0.054 | [-0.647, +0.538] |
| RNDRUSDT | 7 | +0.682 | [-1.212, +2.577] |
| RSRUSDT | 3 | +0.502 | [-1.410, +2.413] |
| RUNEUSDT | 18 | +0.384 | [-0.485, +1.252] |
| RVNUSDT | 3 | -0.225 | [-1.852, +1.402] |
| SANDUSDT | 42 | +0.040 | [-0.487, +0.567] |
| SEIUSDT | 16 | -0.196 | [-0.815, +0.422] |
| SOLUSDT | 232 | +0.239 | [-0.011, +0.489] |
| STMXUSDT | 12 | -0.278 | [-1.057, +0.502] |
| STORJUSDT | 10 | +0.289 | [-1.265, +1.844] |
| STXUSDT | 5 | -0.713 | [-1.093, -0.333] |
| SUIUSDT | 71 | +0.238 | [-0.280, +0.756] |
| SUSHIUSDT | 36 | +0.056 | [-0.425, +0.536] |
| SXPUSDT | 36 | +0.049 | [-0.490, +0.588] |
| THETAUSDT | 25 | -0.441 | [-0.864, -0.017] |
| TIAUSDT | 35 | -0.127 | [-0.570, +0.315] |
| TOMOUSDT | 14 | -0.317 | [-0.625, -0.009] |
| TONUSDT | 4 | -0.193 | [-1.166, +0.779] |
| TRBUSDT | 30 | +0.237 | [-0.720, +1.193] |
| TRUMPUSDT | 24 | +0.014 | [-0.838, +0.866] |
| TRXUSDT | 82 | +0.104 | [-0.283, +0.491] |
| TURBOUSDT | 5 | -0.646 | [-1.208, -0.083] |
| UMAUSDT | 4 | -0.872 | [-1.279, -0.466] |
| UNFIUSDT | 23 | -0.600 | [-0.961, -0.238] |
| UNIUSDT | 46 | +0.066 | [-0.424, +0.557] |
| UXLINKUSDT | 4 | +0.105 | [-0.940, +1.150] |
| VETUSDT | 31 | +1.128 | [-0.689, +2.946] |
| VIRTUALUSDT | 4 | -0.084 | [-1.054, +0.886] |
| VOXELUSDT | 4 | -0.248 | [-1.764, +1.267] |
| WAVESUSDT | 36 | +0.582 | [-0.360, +1.524] |
| WIFUSDT | 79 | +0.086 | [-0.329, +0.501] |
| WLDUSDT | 65 | +0.064 | [-0.261, +0.389] |
| XLMUSDT | 62 | +0.112 | [-0.373, +0.598] |
| XMRUSDT | 19 | -0.519 | [-0.906, -0.132] |
| XRPUSDT | 275 | +0.080 | [-0.167, +0.327] |
| XTZUSDT | 31 | -0.220 | [-0.654, +0.214] |
| YFIIUSDT | 3 | +0.170 | [-1.392, +1.731] |
| YFIUSDT | 17 | +0.032 | [-0.817, +0.882] |
| ZECUSDT | 27 | +0.092 | [-0.558, +0.742] |
| ZILUSDT | 15 | +0.017 | [-0.726, +0.759] |
| ZRXUSDT | 4 | +0.789 | [-1.375, +2.953] |

29 símbolos del universo sin operaciones en este tramo.

## Holdout

Ventana 2025-09-09 → 2026-11-03 · n=1256 · avgR neto +0.027 [-0.083, +0.136] · bruto +0.075 · acierto 31% · duración mediana 2.5 días

Control nulo: media -0.034, p95 +0.064

**Robustez** (informativa, no decide): costos ×1.5 → +0.005 [-0.104, +0.115] · sin las 10 mejores → -0.085 [-0.168, -0.003]

| Tramo | n | avgR neto |
|---|---|---|
| 2025-09-09 → 2025-12-23 | 314 | +0.105 |
| 2025-12-23 → 2026-04-11 | 314 | +0.058 |
| 2026-04-11 → 2026-07-20 | 314 | -0.106 |
| 2026-07-20 → 2026-11-02 | 314 | +0.050 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000LUNCUSDT | 5 | -0.508 | [-1.577, +0.561] |
| 1000PEPEUSDT | 61 | +0.112 | [-0.421, +0.644] |
| ACEUSDT | 7 | -0.588 | [-1.182, +0.005] |
| ADAUSDT | 61 | +0.169 | [-0.301, +0.640] |
| AIAUSDT | 1 | +2.945 | — |
| AKEUSDT | 13 | +0.547 | [-0.814, +1.908] |
| ARBUSDT | 10 | -0.639 | [-1.120, -0.159] |
| ARIAUSDT | 3 | +0.806 | [-1.160, +2.772] |
| ASTERUSDT | 13 | -0.076 | [-0.839, +0.686] |
| AVAXUSDT | 40 | +0.053 | [-0.419, +0.525] |
| AXSUSDT | 3 | -0.173 | [-1.736, +1.389] |
| BANKUSDT | 2 | -0.553 | [-0.696, -0.409] |
| BCHUSDT | 16 | -0.609 | [-0.971, -0.246] |
| BEATUSDT | 5 | -0.227 | [-1.113, +0.660] |
| BERAUSDT | 5 | +0.567 | [-0.505, +1.639] |
| BIOUSDT | 4 | -0.296 | [-1.160, +0.568] |
| BNBUSDT | 62 | +0.040 | [-0.437, +0.516] |
| BSBUSDT | 3 | +0.185 | [-0.984, +1.354] |
| BTCUSDT | 66 | +0.149 | [-0.491, +0.788] |
| BTWUSDT | 6 | +0.041 | [-1.645, +1.727] |
| CYSUSDT | 4 | +0.401 | [-1.051, +1.853] |
| DASHUSDT | 7 | -0.217 | [-1.031, +0.597] |
| DEXEUSDT | 1 | +0.419 | — |
| DOGEUSDT | 57 | +0.069 | [-0.410, +0.547] |
| ENAUSDT | 32 | +0.144 | [-0.455, +0.743] |
| ENJUSDT | 4 | +0.026 | [-1.226, +1.278] |
| ESPORTSUSDT | 1 | +0.340 | — |
| ETHUSDT | 62 | +0.279 | [-0.444, +1.001] |
| EVAAUSDT | 1 | +0.122 | — |
| FARTCOINUSDT | 13 | +0.091 | [-0.717, +0.899] |
| FILUSDT | 4 | -0.311 | [-1.770, +1.149] |
| HUSDT | 1 | +0.546 | — |
| HYPEUSDT | 69 | -0.012 | [-0.464, +0.441] |
| IPUSDT | 3 | +0.755 | [-0.211, +1.720] |
| LABUSDT | 10 | +0.050 | [-0.742, +0.842] |
| LIGHTUSDT | 2 | +1.571 | [+0.585, +2.557] |
| LINKUSDT | 52 | -0.366 | [-0.711, -0.021] |
| LSKUSDT | 5 | -0.128 | [-1.226, +0.970] |
| LTCUSDT | 12 | -0.257 | [-0.834, +0.319] |
| LUNA2USDT | 4 | +0.011 | [-1.567, +1.589] |
| MUSDT | 5 | -0.606 | [-1.002, -0.210] |
| MYXUSDT | 9 | -0.017 | [-0.579, +0.544] |
| NEARUSDT | 27 | -0.352 | [-0.709, +0.004] |
| ONDOUSDT | 6 | -0.618 | [-1.272, +0.036] |
| ORDIUSDT | 5 | +0.234 | [-1.250, +1.719] |
| PENGUUSDT | 11 | -0.089 | [-0.825, +0.647] |
| PIPPINUSDT | 16 | +0.385 | [-0.534, +1.305] |
| PIXELUSDT | 6 | -0.555 | [-0.910, -0.201] |
| POWERUSDT | 3 | +0.320 | [-0.318, +0.957] |
| PUMPUSDT | 28 | -0.076 | [-0.601, +0.448] |
| QNTUSDT | 4 | -0.772 | [-1.279, -0.265] |
| RAVEUSDT | 3 | +0.367 | [-1.161, +1.895] |
| RIVERUSDT | 13 | +0.060 | [-0.682, +0.802] |
| SIRENUSDT | 12 | -0.507 | [-0.921, -0.093] |
| SKYAIUSDT | 10 | -0.412 | [-1.252, +0.428] |
| SOLUSDT | 64 | +0.194 | [-0.395, +0.782] |
| STOUSDT | 4 | +1.504 | [-0.930, +3.938] |
| STRKUSDT | 1 | -1.026 | — |
| SUIUSDT | 67 | +0.162 | [-0.425, +0.750] |
| SYNUSDT | 3 | +0.708 | [-1.027, +2.442] |
| TAOUSDT | 17 | +0.031 | [-0.410, +0.472] |
| TLMUSDT | 6 | -0.858 | [-1.186, -0.529] |
| TNSRUSDT | 3 | -0.332 | [-1.776, +1.112] |
| TONUSDT | 5 | -0.533 | [-1.170, +0.105] |
| TRUMPUSDT | 16 | -0.611 | [-0.965, -0.257] |
| TUTUSDT | 3 | -0.263 | [-1.046, +0.520] |
| UNIUSDT | 11 | -0.579 | [-1.034, -0.125] |
| VELVETUSDT | 2 | +0.119 | [-0.243, +0.480] |
| WLDUSDT | 25 | -0.347 | [-0.693, -0.001] |
| XLMUSDT | 9 | -0.253 | [-0.816, +0.311] |
| XMRUSDT | 3 | +0.498 | [-1.276, +2.271] |
| XPLUSDT | 4 | -0.229 | [-0.861, +0.402] |
| XRPUSDT | 68 | +0.119 | [-0.479, +0.717] |
| ZECUSDT | 57 | +0.469 | [-0.406, +1.344] |

119 símbolos del universo sin operaciones en este tramo.
