# 2026-11-24-volatilidad-realizada-1d — RECHAZADA

- **Estrategia:** `volatilidad_realizada` {"ventana": 30, "k": 3, "atr_n": 14, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 1d · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-24T06:45:50+00:00 · commit `77552e6`

## Hipótesis

Mecanismo: preferencia minorista por activos «lotería». La demanda por monedas de varianza alta las sobrevalúa y rinden menos las semanas siguientes; el comprador de lotería pierde y quien vende esa varianza (corto de alta volatilidad) o prefiere lo estable (largo de baja volatilidad) cobra. La señal es la dispersión de los retornos, no su nivel pasado: distinta de tendencia y de momentum.
Regla, UNA sola configuración fijada antes de correr, tomada de la idea (ventana de 30 días, la misma que el efecto MAX para no abrir otro grado de libertad), no de datos: cada vela diaria `t`, entre los símbolos vigentes del top 20 del mes, VOL = desviación estándar de los retornos diarios de las últimas 30 velas hasta el cierre de `t` (ventana completa: con huecos o historia corta no hay señal). Largo los 3 de menor VOL y corto los 3 de mayor (sólo si hay al menos 6 vigentes). Sentido: el de la fuente; el inverso NO se prueba, ni otras ventanas ni otros estimadores de volatilidad. Entrada en la apertura de la vela siguiente. Stop a 2 ATR(14) desde la entrada y trailing a 2 ATR desde el mejor precio desde la entrada (lo mueve el motor); sin objetivo; tope 7 velas diarias. Costos: 0.1% por lado (0.05% comisión + 0.05% deslizamiento) y funding de futuros.
Es una ETAPA 1 (cribado, `reglas-de-medicion.md` § Cribado): mide sólo desarrollo, con el criterio de desarrollo completo y sin mirar nunca el holdout. Si pasa todo, queda NO_CONCLUYENTE por «holdout no mirado» y se pre-registra la etapa 2 con la misma regla y los mismos parámetros.
Riesgos declarados: (1) evidencia B-: el premio de la fuente está en monedas chicas y un análisis independiente no lo halla en el top 50; en el top 20 debería ser más débil; (2) es la 3.ª prueba de la familia «lotería» (MAX −0.068 y beta a la baja −0.055 no pasaron el cribado), así que el ajuste por pruebas pesa; (3) el corto de alta volatilidad pierde en mercado alcista y el largo de baja volatilidad (stablecoin-like, ATR chico) tiene stop muy cercano en precio: el control nulo y los tramos son el contrapeso; (4) la volatilidad cambia despacio: las entradas se repiten en los mismos símbolos y las muestras se solapan, el IC de ±2 EE es optimista; (5) el holdout se declara contaminado por la familia.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 2020 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.004 [-0.030, +0.038] | ❌ |
| ajustado por 6 prueba(s) de la familia: avgR − 2.64 EE > 0 | +0.004 − 2.64×0.017 = -0.041 | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-04-02:+0.02R 2021-07-24:-0.02R 2022-12-19:+0.00R 2024-04-28:+0.01R): depende del régimen; la dispersión entre tramos (0.03R) supera el doble del avgR (0.004R) | ❌ |
| tramos positivos ≥ 3 | 3/4 | ✅ |
| supera el percentil 95 del control nulo | +0.004 vs p95 +0.064 | ❌ |
| alcance: duración mediana ≤ 14 días | 7.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (+0.004 [-0.030, +0.038]); desarrollo: falla «ajustado por 6 prueba(s) de la familia: avgR − 2.64 EE > 0» (+0.004 − 2.64×0.017 = -0.041); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-04-02:+0.02R 2021-07-24:-0.02R 2022-12-19:+0.00R 2024-04-28:+0.01R): depende del régimen; la dispersión entre tramos (0.03R) supera el doble del avgR (0.004R)); desarrollo: falla «supera el percentil 95 del control nulo» (+0.004 vs p95 +0.064)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `corte_transversal`:** 6 (esta incluida; 1 medidas fuera de este repo)
  - `2026-11-18-momentum-transversal-1d`: RECHAZADA, desarrollo -0.012
  - `2026-11-19-momentum-transversal-1d-ret1`: RECHAZADA, desarrollo -0.022
  - `2026-11-20-efecto-max-1d`: RECHAZADA, desarrollo -0.068
  - `2026-11-23-beta-baja-1d`: RECHAZADA, desarrollo -0.055
- **Holdout contaminado:** sí
- **Pre-registro:** commit `77552e6` del 2026-11-24T06:41:12Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -30.52 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=2020 · avgR neto +0.004 [-0.030, +0.038] · bruto +0.025 · acierto 48% · duración mediana 7.0 días

Control nulo: media +0.018, p95 +0.064

**Robustez** (informativa, no decide): costos ×1.5 → -0.003 [-0.037, +0.031] · sin las 10 mejores → -0.018 [-0.049, +0.013]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-02 → 2021-07-23 | 505 | +0.017 |
| 2021-07-24 → 2022-12-18 | 505 | -0.018 |
| 2022-12-19 → 2024-04-28 | 505 | +0.005 |
| 2024-04-28 → 2025-09-08 | 505 | +0.012 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000FLOKIUSDT | 3 | +0.226 | [-0.873, +1.325] |
| 1000PEPEUSDT | 35 | -0.117 | [-0.340, +0.106] |
| 1000RATSUSDT | 5 | +0.215 | [-0.573, +1.002] |
| 1000SATSUSDT | 8 | +0.072 | [-0.401, +0.545] |
| 1000SHIBUSDT | 21 | -0.051 | [-0.277, +0.176] |
| 1MBABYDOGEUSDT | 1 | +0.456 | — |
| AAVEUSDT | 4 | -0.042 | [-0.771, +0.687] |
| ADAUSDT | 49 | -0.162 | [-0.342, +0.019] |
| ALGOUSDT | 1 | +0.612 | — |
| ALICEUSDT | 10 | +0.043 | [-0.386, +0.471] |
| ALPACAUSDT | 5 | +0.002 | [+0.000, +0.003] |
| APEUSDT | 8 | +0.027 | [-0.396, +0.451] |
| APTUSDT | 3 | +0.388 | [-0.204, +0.981] |
| ARBUSDT | 5 | -0.444 | [-0.920, +0.033] |
| ARKUSDT | 2 | +0.216 | [-0.171, +0.603] |
| ARPAUSDT | 5 | -0.060 | [-0.659, +0.538] |
| ATOMUSDT | 23 | +0.025 | [-0.208, +0.259] |
| AUCTIONUSDT | 2 | -0.022 | [-0.123, +0.080] |
| AVAXUSDT | 15 | -0.256 | [-0.548, +0.037] |
| AXSUSDT | 21 | +0.008 | [-0.321, +0.338] |
| BAKEUSDT | 3 | -0.015 | [-0.473, +0.443] |
| BANDUSDT | 9 | -0.054 | [-0.438, +0.330] |
| BATUSDT | 6 | +0.035 | [-0.606, +0.676] |
| BCHUSDT | 26 | +0.148 | [-0.129, +0.426] |
| BELUSDT | 2 | -0.138 | [-0.403, +0.128] |
| BIGTIMEUSDT | 4 | +0.227 | [-0.201, +0.654] |
| BIOUSDT | 2 | -0.323 | [-1.201, +0.554] |
| BLURUSDT | 3 | -0.014 | [-0.728, +0.700] |
| BLZUSDT | 10 | -0.428 | [-0.912, +0.057] |
| BNBUSDT | 246 | +0.051 | [-0.053, +0.155] |
| BNTUSDT | 3 | +0.023 | [-0.301, +0.347] |
| BNXUSDT | 8 | -0.267 | [-0.609, +0.075] |
| BOMEUSDT | 1 | +0.726 | — |
| BTCUSDT | 301 | +0.053 | [-0.050, +0.155] |
| CFXUSDT | 1 | +0.332 | — |
| CHRUSDT | 2 | +0.157 | [-0.504, +0.819] |
| CHZUSDT | 9 | -0.108 | [-0.484, +0.268] |
| CKBUSDT | 7 | -0.132 | [-0.617, +0.353] |
| COMPUSDT | 1 | +0.048 | — |
| CRVUSDT | 7 | -0.024 | [-0.534, +0.486] |
| CTSIUSDT | 6 | +0.136 | [-0.501, +0.774] |
| DASHUSDT | 5 | -0.326 | [-0.791, +0.140] |
| DOGEUSDT | 42 | +0.032 | [-0.149, +0.212] |
| DOTUSDT | 11 | +0.129 | [-0.509, +0.766] |
| DYDXUSDT | 15 | -0.206 | [-0.553, +0.141] |
| ENAUSDT | 17 | -0.062 | [-0.329, +0.205] |
| EOSUSDT | 23 | +0.301 | [+0.111, +0.492] |
| ETCUSDT | 34 | -0.027 | [-0.223, +0.170] |
| ETHFIUSDT | 3 | +0.399 | [+0.200, +0.597] |
| ETHUSDT | 145 | -0.020 | [-0.150, +0.111] |
| FARTCOINUSDT | 21 | -0.189 | [-0.448, +0.070] |
| FILUSDT | 15 | -0.456 | [-0.723, -0.189] |
| FLMUSDT | 4 | -0.074 | [-0.635, +0.486] |
| FRONTUSDT | 1 | +0.831 | — |
| FTMUSDT | 24 | +0.088 | [-0.199, +0.375] |
| FTTUSDT | 4 | -0.018 | [-0.034, -0.002] |
| FUNUSDT | 5 | +0.094 | [-0.917, +1.105] |
| GALAUSDT | 19 | -0.001 | [-0.272, +0.270] |
| GMTUSDT | 12 | +0.036 | [-0.313, +0.385] |
| GRTUSDT | 3 | -0.008 | [-0.764, +0.748] |
| HNTUSDT | 5 | +0.142 | [-0.090, +0.374] |
| HYPERUSDT | 1 | +0.418 | — |
| ICPUSDT | 4 | +0.122 | [-0.775, +1.019] |
| INJUSDT | 4 | +0.043 | [-0.542, +0.629] |
| IOSTUSDT | 3 | +0.347 | [+0.128, +0.567] |
| IOTXUSDT | 2 | +0.361 | [-0.333, +1.054] |
| JUPUSDT | 2 | +0.448 | [+0.406, +0.491] |
| KAITOUSDT | 1 | +0.571 | — |
| KLAYUSDT | 2 | +0.132 | [+0.093, +0.171] |
| KNCUSDT | 5 | +0.274 | [-0.262, +0.810] |
| KSMUSDT | 4 | -0.075 | [-0.521, +0.371] |
| LAYERUSDT | 1 | +0.322 | — |
| LDOUSDT | 1 | +0.790 | — |
| LENDUSDT | 2 | +0.213 | [-0.753, +1.180] |
| LINAUSDT | 10 | -0.483 | [-0.829, -0.138] |
| LINKUSDT | 29 | -0.181 | [-0.434, +0.072] |
| LITUSDT | 2 | +0.579 | [-2.599, +3.758] |
| LPTUSDT | 3 | +0.302 | [+0.143, +0.461] |
| LQTYUSDT | 1 | +0.057 | — |
| LRCUSDT | 2 | +0.232 | [-0.046, +0.511] |
| LTCUSDT | 36 | +0.116 | [-0.104, +0.335] |
| LUNAUSDT | 7 | +0.273 | [-0.363, +0.910] |
| MANAUSDT | 3 | -0.300 | [-1.126, +0.526] |
| MASKUSDT | 11 | -0.061 | [-0.395, +0.272] |
| MATICUSDT | 17 | -0.077 | [-0.377, +0.222] |
| MKRUSDT | 1 | -0.023 | — |
| MOODENGUSDT | 4 | +0.155 | [-0.433, +0.742] |
| MTLUSDT | 2 | +0.090 | [-0.620, +0.799] |
| MYXUSDT | 1 | -1.010 | — |
| NEARUSDT | 11 | +0.289 | [-0.186, +0.763] |
| NEIROUSDT | 10 | +0.192 | [-0.193, +0.577] |
| NEOUSDT | 5 | -0.217 | [-0.636, +0.202] |
| NOTUSDT | 5 | +0.356 | [+0.069, +0.642] |
| OCEANUSDT | 2 | -0.605 | [-0.917, -0.292] |
| OMGUSDT | 4 | -0.019 | [-0.748, +0.710] |
| OMUSDT | 1 | -0.058 | — |
| ONGUSDT | 2 | +0.204 | [-0.013, +0.420] |
| ONTUSDT | 1 | -0.150 | — |
| OPUSDT | 6 | +0.111 | [-0.352, +0.573] |
| ORDIUSDT | 11 | -0.294 | [-0.676, +0.087] |
| PENGUUSDT | 1 | +0.609 | — |
| PEOPLEUSDT | 11 | +0.068 | [-0.412, +0.547] |
| PNUTUSDT | 10 | -0.045 | [-0.419, +0.328] |
| POPCATUSDT | 3 | +0.320 | [-0.167, +0.807] |
| PUMPUSDT | 5 | -0.176 | [-0.459, +0.107] |
| RAREUSDT | 3 | -0.398 | [-0.908, +0.112] |
| REEFUSDT | 8 | +0.268 | [-0.823, +1.358] |
| RNDRUSDT | 3 | -0.792 | [-0.872, -0.712] |
| RUNEUSDT | 7 | -0.147 | [-0.553, +0.259] |
| RVNUSDT | 2 | +0.298 | [-0.390, +0.986] |
| SANDUSDT | 8 | +0.076 | [-0.375, +0.526] |
| SEIUSDT | 5 | -0.120 | [-0.921, +0.680] |
| SOLUSDT | 17 | -0.197 | [-0.453, +0.059] |
| STMXUSDT | 6 | +0.087 | [-0.262, +0.435] |
| STORJUSDT | 7 | -0.117 | [-0.671, +0.437] |
| SUIUSDT | 7 | -0.269 | [-0.852, +0.314] |
| SUSHIUSDT | 9 | -0.175 | [-0.553, +0.202] |
| SXPUSDT | 9 | +0.038 | [-0.343, +0.419] |
| THETAUSDT | 4 | -0.105 | [-0.736, +0.526] |
| TIAUSDT | 7 | -0.259 | [-0.722, +0.204] |
| TOMOUSDT | 10 | -0.086 | [-0.458, +0.286] |
| TRBUSDT | 23 | -0.263 | [-0.559, +0.033] |
| TRUMPUSDT | 6 | +0.074 | [-0.594, +0.743] |
| TRXUSDT | 27 | +0.271 | [-0.107, +0.648] |
| TURBOUSDT | 3 | -0.388 | [-0.467, -0.310] |
| UMAUSDT | 2 | +0.161 | [-0.918, +1.240] |
| UNFIUSDT | 11 | -0.049 | [-0.553, +0.456] |
| UNIUSDT | 7 | -0.290 | [-0.829, +0.248] |
| UXLINKUSDT | 3 | +0.411 | [+0.042, +0.780] |
| VETUSDT | 21 | -0.369 | [-0.627, -0.111] |
| VIRTUALUSDT | 1 | +0.174 | — |
| VOXELUSDT | 4 | +0.127 | [-0.447, +0.700] |
| WAVESUSDT | 10 | -0.131 | [-0.562, +0.300] |
| WIFUSDT | 29 | -0.195 | [-0.404, +0.013] |
| WLDUSDT | 20 | +0.257 | [-0.060, +0.574] |
| XLMUSDT | 24 | -0.082 | [-0.367, +0.204] |
| XMRUSDT | 7 | -0.001 | [-0.504, +0.501] |
| XRPUSDT | 147 | +0.115 | [-0.073, +0.303] |
| XTZUSDT | 4 | +0.020 | [-0.647, +0.687] |
| YFIUSDT | 6 | -0.440 | [-0.955, +0.076] |
| ZECUSDT | 8 | +0.191 | [-0.244, +0.627] |
| ZILUSDT | 2 | +0.863 | [-0.499, +2.225] |
| ZRXUSDT | 3 | +0.244 | [-0.245, +0.734] |

46 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
