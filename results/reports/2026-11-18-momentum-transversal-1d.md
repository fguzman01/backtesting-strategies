# 2026-11-18-momentum-transversal-1d — RECHAZADA

- **Estrategia:** `momentum_transversal` {"lookback": 7, "k": 3, "atr_n": 14, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 1d · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-18T06:44:48+00:00 · commit `79f2142`

## Hipótesis

Mecanismo: la atención y los flujos llegan escalonados entre monedas; las que más subieron en la última semana siguen siendo comparadas favorablemente por quienes llegan tarde, y las que más cayeron siguen liberando posiciones de quienes capitulan de a poco. Quien pierde es el que vende a destiempo contra el flujo (o compra la caída ya agotada). Regla, UNA sola configuración fijada antes de correr, desde la literatura y no desde datos: cada vela diaria, entre los símbolos vigentes del top 20 del mes se rankea el retorno de 7 cierres (el horizonte de 1 semana del factor de momentum de Liu, Tsyvinski & Wu; la idea #17 decía «1–3 días» y se fija 7 porque es el horizonte con soporte publicado, no por mirar resultados); largo los 3 mejores, corto los 3 peores (≈ 15% de 20 en cada extremo; sólo si hay al menos 6 vigentes). Sentido: momentum, fijado antes de correr; la reversión no se prueba aparte. Entrada en la apertura de la vela siguiente. Stop a 2 ATR(14) desde la entrada y trailing a 2 ATR desde el mejor precio desde la entrada (lo mueve el motor); sin objetivo; tope 5 velas diarias (5 días). Con stop de 2 ATR diario (~5–7% en cripto líquida) la comisión de 0.1% por lado (0.05% + 0.05% de deslizamiento) pesa ~0.03–0.04R; el riesgo central es que el efecto de 7 días se agote antes de los 5 días de tenencia o que la parte corta pague caro el rebote de los más castigados (squeeze). Cupo de 3 por dirección: lo mismo que operaría el bot con TREND_4H y es el número natural de la regla. Universo dinámico top 20 (sin sesgo de supervivencia: los retirados que más cayeron entran, y como cortos ayudarían: esto es correcto y buscado). Criterio exigente por defecto.
Riesgos declarados: (1) la señal se repite todos los días para el mismo símbolo mientras siga en el extremo; el motor opera una posición a la vez por símbolo, así que las operaciones no son independientes entre símbolos (comparten el mismo mercado): el IC con ±2 EE es optimista, y el control nulo y los tramos son el contrapeso; (2) la dirección neta puede acumular riesgo de mercado (3 largos vs 3 cortos no está neutralizado por beta); (3) el holdout se declara contaminado (ver `holdout_contaminado`).

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 2857 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | -0.012 [-0.045, +0.021] | ❌ |
| ajustado por 2 prueba(s) de la familia: avgR − 2.24 EE > 0 | -0.012 − 2.24×0.016 = -0.049 | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-04-02:+0.00R 2021-08-07:-0.02R 2022-12-22:-0.05R 2024-04-30:+0.02R): depende del régimen; la dispersión entre tramos (0.06R) supera el doble del avgR (-0.012R) | ❌ |
| tramos positivos ≥ 3 | 2/4 | ❌ |
| supera el percentil 95 del control nulo | -0.012 vs p95 +0.032 | ❌ |
| alcance: duración mediana ≤ 14 días | 5.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (-0.012 [-0.045, +0.021]); desarrollo: falla «ajustado por 2 prueba(s) de la familia: avgR − 2.24 EE > 0» (-0.012 − 2.24×0.016 = -0.049); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-04-02:+0.00R 2021-08-07:-0.02R 2022-12-22:-0.05R 2024-04-30:+0.02R): depende del régimen; la dispersión entre tramos (0.06R) supera el doble del avgR (-0.012R)); desarrollo: falla «tramos positivos ≥ 3» (2/4); desarrollo: falla «supera el percentil 95 del control nulo» (-0.012 vs p95 +0.032)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `corte_transversal`:** 2 (esta incluida; 1 medidas fuera de este repo)
- **Holdout contaminado:** sí
- **Pre-registro:** commit `79f2142` del 2026-11-18T06:41:39Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -72.09 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=2857 · avgR neto -0.012 [-0.045, +0.021] · bruto -0.001 · acierto 46% · duración mediana 5.0 días

Control nulo: media -0.002, p95 +0.032

**Robustez** (informativa, no decide): costos ×1.5 → -0.018 [-0.051, +0.015] · sin las 10 mejores → -0.037 [-0.060, -0.013]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-02 → 2021-08-07 | 715 | +0.004 |
| 2021-08-07 → 2022-12-22 | 714 | -0.021 |
| 2022-12-22 → 2024-04-29 | 714 | -0.046 |
| 2024-04-30 → 2025-09-08 | 714 | +0.016 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 12 | -0.019 | [-0.220, +0.182] |
| 1000FLOKIUSDT | 10 | -0.117 | [-0.548, +0.314] |
| 1000LUNCUSDT | 3 | +0.060 | [-0.128, +0.248] |
| 1000PEPEUSDT | 68 | +0.021 | [-0.144, +0.186] |
| 1000RATSUSDT | 5 | -0.604 | [-0.896, -0.312] |
| 1000SATSUSDT | 13 | -0.102 | [-0.333, +0.128] |
| 1000SHIBUSDT | 45 | -0.139 | [-0.291, +0.013] |
| 1MBABYDOGEUSDT | 3 | +0.382 | [-0.246, +1.009] |
| AAVEUSDT | 29 | +0.122 | [-0.152, +0.395] |
| ADAUSDT | 109 | +0.047 | [-0.084, +0.178] |
| ALGOUSDT | 5 | +0.159 | [-0.402, +0.721] |
| ALICEUSDT | 8 | +0.190 | [-0.271, +0.651] |
| ALPACAUSDT | 6 | -0.037 | [-0.073, -0.001] |
| APEUSDT | 26 | +0.039 | [-0.194, +0.272] |
| APTUSDT | 15 | +0.055 | [-0.227, +0.336] |
| ARBUSDT | 18 | -0.189 | [-0.451, +0.072] |
| ARKUSDT | 4 | +0.073 | [-0.096, +0.243] |
| ARPAUSDT | 3 | +0.341 | [+0.118, +0.565] |
| ATOMUSDT | 43 | -0.032 | [-0.262, +0.197] |
| AUCTIONUSDT | 6 | +0.025 | [-0.072, +0.122] |
| AVAXUSDT | 72 | -0.095 | [-0.264, +0.074] |
| AXSUSDT | 24 | +0.027 | [-0.186, +0.241] |
| BAKEUSDT | 2 | -0.179 | [-0.483, +0.124] |
| BANDUSDT | 12 | -0.203 | [-0.481, +0.075] |
| BATUSDT | 15 | -0.060 | [-0.440, +0.320] |
| BCHUSDT | 53 | -0.119 | [-0.264, +0.026] |
| BELUSDT | 6 | -0.009 | [-0.407, +0.389] |
| BIGTIMEUSDT | 4 | -0.244 | [-0.587, +0.099] |
| BIOUSDT | 1 | -0.762 | — |
| BLURUSDT | 2 | -0.230 | [-1.616, +1.157] |
| BLZUSDT | 11 | +0.290 | [-0.340, +0.920] |
| BNBUSDT | 158 | +0.024 | [-0.124, +0.171] |
| BNTUSDT | 2 | -0.091 | [-0.345, +0.163] |
| BNXUSDT | 6 | -0.028 | [-1.292, +1.236] |
| BOMEUSDT | 10 | -0.339 | [-0.690, +0.011] |
| BTCUSDT | 129 | +0.045 | [-0.080, +0.169] |
| CFXUSDT | 12 | -0.047 | [-0.400, +0.307] |
| CHRUSDT | 5 | +0.125 | [-0.199, +0.450] |
| CHZUSDT | 31 | -0.067 | [-0.276, +0.141] |
| CKBUSDT | 2 | +0.048 | [-1.172, +1.269] |
| COMPUSDT | 13 | +0.063 | [-0.297, +0.423] |
| CRVUSDT | 16 | +0.037 | [-0.250, +0.324] |
| CTSIUSDT | 4 | -0.272 | [-0.788, +0.244] |
| DASHUSDT | 5 | -0.149 | [-0.740, +0.443] |
| DOGEUSDT | 79 | +0.032 | [-0.119, +0.183] |
| DOTUSDT | 35 | -0.191 | [-0.371, -0.010] |
| DYDXUSDT | 26 | -0.018 | [-0.237, +0.201] |
| EGLDUSDT | 2 | +1.041 | [+0.150, +1.933] |
| ENAUSDT | 31 | -0.041 | [-0.354, +0.272] |
| ENJUSDT | 3 | -0.214 | [-0.796, +0.367] |
| ENSUSDT | 2 | -0.105 | [-0.170, -0.039] |
| EOSUSDT | 51 | -0.089 | [-0.240, +0.062] |
| ETCUSDT | 51 | +0.203 | [-0.184, +0.589] |
| ETHFIUSDT | 3 | +0.092 | [-0.913, +1.096] |
| ETHUSDT | 90 | -0.029 | [-0.164, +0.107] |
| FARTCOINUSDT | 26 | -0.091 | [-0.319, +0.138] |
| FETUSDT | 1 | +0.277 | — |
| FILUSDT | 35 | +0.099 | [-0.177, +0.374] |
| FLMUSDT | 3 | +0.242 | [-0.110, +0.594] |
| FRONTUSDT | 2 | -0.139 | [-1.070, +0.792] |
| FTMUSDT | 41 | +0.117 | [-0.096, +0.331] |
| FTTUSDT | 2 | -0.024 | [-0.046, -0.001] |
| FUNUSDT | 3 | +0.654 | [+0.566, +0.741] |
| GALAUSDT | 24 | +0.161 | [-0.053, +0.375] |
| GMTUSDT | 22 | -0.145 | [-0.325, +0.035] |
| GRTUSDT | 4 | -0.440 | [-0.977, +0.097] |
| HBARUSDT | 4 | +0.029 | [-0.372, +0.431] |
| HIGHUSDT | 3 | -0.073 | [-0.697, +0.550] |
| HNTUSDT | 4 | +0.034 | [-0.217, +0.286] |
| HYPERUSDT | 4 | +0.153 | [-0.031, +0.337] |
| ICPUSDT | 2 | -0.038 | [-1.716, +1.641] |
| INJUSDT | 11 | -0.041 | [-0.383, +0.301] |
| IOSTUSDT | 7 | -0.230 | [-0.645, +0.185] |
| IOTXUSDT | 3 | -0.159 | [-0.538, +0.220] |
| JASMYUSDT | 4 | +0.123 | [-0.704, +0.951] |
| JUPUSDT | 3 | -0.476 | [-0.777, -0.175] |
| KAITOUSDT | 3 | +0.226 | [-0.504, +0.956] |
| KNCUSDT | 6 | +0.183 | [-0.357, +0.723] |
| KSMUSDT | 2 | -0.442 | [-0.900, +0.016] |
| LAYERUSDT | 4 | +0.136 | [-0.035, +0.307] |
| LDOUSDT | 9 | -0.197 | [-0.587, +0.194] |
| LENDUSDT | 4 | -0.114 | [-0.308, +0.080] |
| LINAUSDT | 9 | -0.179 | [-0.458, +0.100] |
| LINKUSDT | 94 | -0.018 | [-0.149, +0.112] |
| LITUSDT | 3 | -0.145 | [-0.807, +0.516] |
| LPTUSDT | 3 | -0.023 | [-0.771, +0.724] |
| LQTYUSDT | 3 | +0.167 | [-0.099, +0.433] |
| LRCUSDT | 4 | -0.093 | [-0.412, +0.226] |
| LTCUSDT | 63 | -0.115 | [-0.260, +0.031] |
| LUNAUSDT | 25 | -0.035 | [-0.466, +0.396] |
| MANAUSDT | 14 | +0.043 | [-0.266, +0.352] |
| MASKUSDT | 13 | -0.237 | [-0.495, +0.022] |
| MATICUSDT | 59 | -0.089 | [-0.257, +0.078] |
| MEWUSDT | 3 | +0.036 | [-0.204, +0.275] |
| MKRUSDT | 5 | -0.317 | [-0.914, +0.280] |
| MOODENGUSDT | 2 | +0.175 | [-0.380, +0.731] |
| MTLUSDT | 6 | +0.216 | [-0.220, +0.652] |
| MYXUSDT | 1 | +29.202 | — |
| NEARUSDT | 26 | -0.045 | [-0.299, +0.209] |
| NEIROUSDT | 11 | +0.226 | [-0.102, +0.555] |
| NEOUSDT | 15 | +0.007 | [-0.272, +0.285] |
| NMRUSDT | 1 | -1.012 | — |
| NOTUSDT | 9 | +0.003 | [-0.453, +0.459] |
| OCEANUSDT | 5 | +0.078 | [-0.630, +0.787] |
| OMGUSDT | 3 | -0.501 | [-1.019, +0.017] |
| OMUSDT | 1 | +0.107 | — |
| ONDOUSDT | 5 | -0.164 | [-0.433, +0.106] |
| ONEUSDT | 2 | +0.686 | [+0.099, +1.272] |
| ONGUSDT | 3 | +0.138 | [-0.165, +0.441] |
| ONTUSDT | 11 | -0.178 | [-0.599, +0.243] |
| OPUSDT | 28 | -0.089 | [-0.266, +0.088] |
| ORDIUSDT | 24 | +0.042 | [-0.178, +0.263] |
| PENGUUSDT | 5 | -0.407 | [-1.053, +0.239] |
| PEOPLEUSDT | 13 | -0.086 | [-0.384, +0.211] |
| PERPUSDT | 1 | -0.917 | — |
| PNUTUSDT | 9 | -0.081 | [-0.393, +0.230] |
| POPCATUSDT | 3 | -0.076 | [-0.216, +0.064] |
| PUMPUSDT | 4 | +0.080 | [-0.119, +0.280] |
| RAREUSDT | 4 | -0.220 | [-0.490, +0.050] |
| REEFUSDT | 11 | +0.211 | [-0.174, +0.597] |
| RNDRUSDT | 3 | +0.152 | [-0.291, +0.595] |
| RSRUSDT | 1 | +0.152 | — |
| RUNEUSDT | 14 | +0.259 | [-0.203, +0.720] |
| RVNUSDT | 3 | -0.168 | [-0.294, -0.042] |
| SANDUSDT | 17 | -0.004 | [-0.358, +0.350] |
| SEIUSDT | 8 | -0.335 | [-0.879, +0.209] |
| SOLUSDT | 104 | +0.021 | [-0.125, +0.166] |
| STMXUSDT | 5 | +0.075 | [-0.567, +0.716] |
| STORJUSDT | 8 | -0.134 | [-0.567, +0.299] |
| SUIUSDT | 39 | +0.142 | [-0.153, +0.436] |
| SUSHIUSDT | 29 | -0.021 | [-0.265, +0.224] |
| SXPUSDT | 18 | -0.252 | [-0.455, -0.050] |
| THETAUSDT | 13 | -0.269 | [-0.496, -0.042] |
| TIAUSDT | 19 | -0.098 | [-0.416, +0.221] |
| TOMOUSDT | 13 | -0.351 | [-0.556, -0.146] |
| TONUSDT | 3 | -0.465 | [-1.089, +0.158] |
| TRBUSDT | 22 | +0.277 | [-0.107, +0.661] |
| TRUMPUSDT | 10 | -0.239 | [-0.575, +0.097] |
| TRXUSDT | 38 | -0.230 | [-0.448, -0.012] |
| TURBOUSDT | 2 | -0.003 | [-1.038, +1.033] |
| UMAUSDT | 3 | +0.055 | [-0.294, +0.404] |
| UNFIUSDT | 11 | -0.154 | [-0.414, +0.107] |
| UNIUSDT | 18 | +0.073 | [-0.226, +0.372] |
| UXLINKUSDT | 2 | +0.365 | [-0.097, +0.827] |
| VETUSDT | 18 | -0.132 | [-0.350, +0.086] |
| VIRTUALUSDT | 2 | -0.343 | [-0.839, +0.152] |
| VOXELUSDT | 4 | +0.049 | [-0.490, +0.588] |
| WAVESUSDT | 20 | +0.008 | [-0.307, +0.322] |
| WIFUSDT | 39 | -0.090 | [-0.304, +0.124] |
| WLDUSDT | 37 | -0.123 | [-0.317, +0.070] |
| XLMUSDT | 26 | +0.094 | [-0.140, +0.329] |
| XMRUSDT | 6 | -0.044 | [-0.423, +0.335] |
| XRPUSDT | 118 | -0.007 | [-0.156, +0.143] |
| XTZUSDT | 12 | -0.206 | [-0.525, +0.113] |
| YFIIUSDT | 3 | +0.307 | [-0.024, +0.639] |
| YFIUSDT | 11 | -0.209 | [-0.450, +0.033] |
| ZECUSDT | 10 | +0.046 | [-0.593, +0.684] |
| ZILUSDT | 9 | -0.185 | [-0.608, +0.237] |
| ZRXUSDT | 3 | -0.035 | [-0.744, +0.673] |

30 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
