# 2026-11-04-trend1d-trailing-atr-real-14d — RECHAZADA

- **Estrategia:** `tendencia_trailing` {"entrada": 20, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 1d · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-04T06:47:12+00:00 · commit `7d459b7`

## Hipótesis

El edge de TREND_1D vive en pocas tendencias largas. El chandelier anterior (máximo móvil de 22 velas − 3 ATR) casi nunca disparó (100% de las salidas por timeout, mediana 14.0 d), así que la hipótesis «trailing» nunca se midió. Aquí el stop inicial de 2 ATR sube con el mejor precio DESDE LA ENTRADA (trailing real del motor, distancia 2 ATR, sin canal corto de 10 velas): las perdedoras se cortan en cuanto la tendencia retrocede 2 ATR desde su máximo y las buenas siguen hasta el tope de 14 días. El mecanismo es el de la persecución de tendencia (los rezagados entran tarde y sostienen el movimiento); el trailing protege la ganancia sin cortar por tiempo. Se fija UNA distancia (2.0 ATR = la del stop inicial, sin barrer k) antes de correr. Costo: 0.1% por lado (comisión + deslizamiento); con stop de 2 ATR diarios (~4-8%) la comisión ronda 0.03-0.05R. Riesgo declarado: la mediana de duración debe quedar ≤ 7 d para entrar en el alcance; la distancia de 2 ATR (la más ajustada coherente con el stop inicial) se eligió justamente para que las operaciones sin continuación salgan en pocos días. Si aun así la mediana supera 7 d es una cuestión de alcance, no de parámetros, y no se prueban otros k. Universo dinámico (los 20 más operados de cada mes, con retirados) para no inflar con sobrevivientes. Cupo 5 por dirección, como TREND_1D en el bot. Holdout declarado contaminado (btc-signal-web ya miró el holdout de TREND_1D): como mucho llega a observación.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 100 | 762 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.049 [-0.027, +0.125] | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-07-23:+0.22R 2021-10-22:-0.09R 2023-03-29:+0.08R 2024-06-18:-0.01R): depende del régimen; la dispersión entre tramos (0.30R) supera el doble del avgR (0.049R) | ❌ |
| tramos positivos ≥ 3 | 2/4 | ❌ |
| supera el percentil 95 del control nulo | +0.049 vs p95 +0.082 | ❌ |
| alcance: duración mediana ≤ 7 días | 6.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (+0.049 [-0.027, +0.125]); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-07-23:+0.22R 2021-10-22:-0.09R 2023-03-29:+0.08R 2024-06-18:-0.01R): depende del régimen; la dispersión entre tramos (0.30R) supera el doble del avgR (0.049R)); desarrollo: falla «tramos positivos ≥ 3» (2/4); desarrollo: falla «supera el percentil 95 del control nulo» (+0.049 vs p95 +0.082)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `tendencia`:** 5 (esta incluida; 4 medidas fuera de este repo)
- **Holdout contaminado:** sí
- **Pre-registro:** commit `7d459b7` del 2026-11-04T06:40:56Z
- **Cupo de cartera:** máx 5 por dirección
- **Peor caída (desarrollo):** -23.44 R
- **Contra la madre `TREND_1D con tope de 14 días` (desarrollo):** hija +0.049 (n=762) vs madre +0.151 (n=612) → diferencia -0.102 [-0.247, +0.042]; peor caída -23.44 vs -21.65 R

## Desarrollo

Ventana 2020-01-01 → 2025-09-08 · n=762 · avgR neto +0.049 [-0.027, +0.125] · bruto +0.080 · acierto 41% · duración mediana 6.0 días

Control nulo: media +0.007, p95 +0.082

**Robustez** (informativa, no decide): costos ×1.5 → +0.042 [-0.034, +0.118] · sin las 10 mejores → -0.021 [-0.082, +0.041]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-07-23 → 2021-10-20 | 191 | +0.215 |
| 2021-10-22 → 2023-03-22 | 191 | -0.088 |
| 2023-03-29 → 2024-06-18 | 190 | +0.078 |
| 2024-06-18 → 2025-08-29 | 190 | -0.009 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 3 | -0.308 | [-1.005, +0.388] |
| 1000FLOKIUSDT | 2 | -0.419 | [-0.551, -0.288] |
| 1000LUNCUSDT | 0 | +0.000 | — |
| 1000PEPEUSDT | 17 | -0.148 | [-0.490, +0.195] |
| 1000RATSUSDT | 0 | +0.000 | — |
| 1000SATSUSDT | 3 | -0.412 | [-0.845, +0.022] |
| 1000SHIBUSDT | 17 | -0.300 | [-0.554, -0.047] |
| 1MBABYDOGEUSDT | 0 | +0.000 | — |
| AAVEUSDT | 7 | +0.017 | [-0.234, +0.268] |
| ACEUSDT | 0 | +0.000 | — |
| ADAUSDT | 43 | +0.172 | [-0.212, +0.555] |
| ALGOUSDT | 0 | +0.000 | — |
| ALICEUSDT | 0 | +0.000 | — |
| ALPACAUSDT | 0 | +0.000 | — |
| APEUSDT | 3 | +0.152 | [-1.453, +1.758] |
| APTUSDT | 2 | -0.444 | [-1.593, +0.704] |
| ARBUSDT | 9 | -0.505 | [-0.725, -0.285] |
| ARIAUSDT | 0 | +0.000 | — |
| ARKUSDT | 0 | +0.000 | — |
| ARPAUSDT | 1 | -0.781 | — |
| ATOMUSDT | 12 | -0.194 | [-0.679, +0.291] |
| AUCTIONUSDT | 1 | -0.109 | — |
| AVAXUSDT | 27 | +0.031 | [-0.247, +0.308] |
| AXSUSDT | 5 | +0.254 | [-0.364, +0.872] |
| BAKEUSDT | 0 | +0.000 | — |
| BANDUSDT | 1 | +0.518 | — |
| BANKUSDT | 0 | +0.000 | — |
| BATUSDT | 0 | +0.000 | — |
| BCHUSDT | 17 | +0.124 | [-0.445, +0.692] |
| BELUSDT | 0 | +0.000 | — |
| BERAUSDT | 0 | +0.000 | — |
| BIGTIMEUSDT | 0 | +0.000 | — |
| BIOUSDT | 0 | +0.000 | — |
| BLURUSDT | 0 | +0.000 | — |
| BLZUSDT | 2 | +0.955 | [-0.698, +2.609] |
| BNBUSDT | 49 | +0.286 | [-0.138, +0.709] |
| BNTUSDT | 0 | +0.000 | — |
| BNXUSDT | 2 | +0.172 | [-2.182, +2.526] |
| BOMEUSDT | 1 | -0.672 | — |
| BTCUSDT | 58 | +0.188 | [-0.120, +0.496] |
| CFXUSDT | 0 | +0.000 | — |
| CHRUSDT | 0 | +0.000 | — |
| CHZUSDT | 6 | +0.040 | [-0.587, +0.667] |
| CKBUSDT | 1 | -1.020 | — |
| COMPUSDT | 1 | +0.207 | — |
| CRVUSDT | 2 | -0.077 | [-0.291, +0.136] |
| CTSIUSDT | 0 | +0.000 | — |
| DASHUSDT | 0 | +0.000 | — |
| DEXEUSDT | 0 | +0.000 | — |
| DOGEUSDT | 36 | -0.088 | [-0.541, +0.364] |
| DOTUSDT | 15 | -0.072 | [-0.470, +0.326] |
| DYDXUSDT | 2 | +0.413 | [-0.431, +1.257] |
| EGLDUSDT | 0 | +0.000 | — |
| ENAUSDT | 8 | +0.248 | [-0.202, +0.699] |
| ENJUSDT | 0 | +0.000 | — |
| ENSUSDT | 0 | +0.000 | — |
| EOSUSDT | 22 | -0.206 | [-0.534, +0.123] |
| ESPORTSUSDT | 0 | +0.000 | — |
| ETCUSDT | 9 | +0.767 | [-1.334, +2.868] |
| ETHFIUSDT | 0 | +0.000 | — |
| ETHUSDT | 45 | +0.270 | [-0.095, +0.635] |
| FARTCOINUSDT | 2 | -0.294 | [-0.625, +0.037] |
| FETUSDT | 1 | -0.375 | — |
| FILUSDT | 9 | -0.173 | [-0.558, +0.212] |
| FLMUSDT | 2 | -0.290 | [-0.536, -0.043] |
| FRONTUSDT | 1 | +0.120 | — |
| FTMUSDT | 12 | +0.058 | [-0.334, +0.450] |
| FTTUSDT | 0 | +0.000 | — |
| FUNUSDT | 0 | +0.000 | — |
| GALAUSDT | 7 | -0.052 | [-0.813, +0.709] |
| GMTUSDT | 4 | +0.011 | [-0.487, +0.508] |
| GRTUSDT | 0 | +0.000 | — |
| HBARUSDT | 1 | -0.431 | — |
| HIFIUSDT | 0 | +0.000 | — |
| HIGHUSDT | 1 | +0.049 | — |
| HNTUSDT | 0 | +0.000 | — |
| HUSDT | 0 | +0.000 | — |
| HYPERUSDT | 0 | +0.000 | — |
| HYPEUSDT | 0 | +0.000 | — |
| ICPUSDT | 0 | +0.000 | — |
| INJUSDT | 4 | -0.352 | [-1.090, +0.385] |
| IOSTUSDT | 0 | +0.000 | — |
| IOTXUSDT | 0 | +0.000 | — |
| IPUSDT | 0 | +0.000 | — |
| JASMYUSDT | 1 | -0.748 | — |
| JUPUSDT | 1 | -0.462 | — |
| KAITOUSDT | 0 | +0.000 | — |
| KLAYUSDT | 0 | +0.000 | — |
| KNCUSDT | 1 | +0.468 | — |
| KSMUSDT | 0 | +0.000 | — |
| LAYERUSDT | 0 | +0.000 | — |
| LDOUSDT | 2 | -0.047 | [-0.659, +0.565] |
| LENDUSDT | 0 | +0.000 | — |
| LINAUSDT | 2 | +0.994 | [-1.404, +3.392] |
| LINKUSDT | 27 | +0.070 | [-0.237, +0.378] |
| LITUSDT | 1 | -0.934 | — |
| LPTUSDT | 1 | -0.590 | — |
| LQTYUSDT | 0 | +0.000 | — |
| LRCUSDT | 0 | +0.000 | — |
| LSKUSDT | 0 | +0.000 | — |
| LTCUSDT | 31 | -0.173 | [-0.393, +0.047] |
| LUNA2USDT | 0 | +0.000 | — |
| LUNAUSDT | 6 | -0.643 | [-0.910, -0.375] |
| MANAUSDT | 3 | -0.526 | [-0.683, -0.370] |
| MASKUSDT | 2 | +0.687 | [-1.907, +3.282] |
| MATICUSDT | 16 | -0.106 | [-0.488, +0.277] |
| MEWUSDT | 0 | +0.000 | — |
| MKRUSDT | 1 | +1.241 | — |
| MOODENGUSDT | 1 | -0.338 | — |
| MTLUSDT | 1 | +0.868 | — |
| MUSDT | 0 | +0.000 | — |
| MYXUSDT | 0 | +0.000 | — |
| NEARUSDT | 6 | +0.167 | [-0.326, +0.660] |
| NEIROUSDT | 1 | -0.410 | — |
| NEOUSDT | 2 | -0.463 | [-0.579, -0.348] |
| NMRUSDT | 0 | +0.000 | — |
| NOTUSDT | 0 | +0.000 | — |
| OCEANUSDT | 3 | +0.105 | [-0.170, +0.381] |
| OMGUSDT | 0 | +0.000 | — |
| OMUSDT | 1 | -0.003 | — |
| ONDOUSDT | 1 | +0.010 | — |
| ONEUSDT | 1 | +0.222 | — |
| ONGUSDT | 0 | +0.000 | — |
| ONTUSDT | 2 | +0.655 | [-0.016, +1.326] |
| OPUSDT | 6 | -0.448 | [-0.761, -0.135] |
| ORDIUSDT | 3 | +0.002 | [-0.902, +0.905] |
| PENGUUSDT | 0 | +0.000 | — |
| PEOPLEUSDT | 3 | +0.089 | [-0.277, +0.455] |
| PERPUSDT | 2 | -0.281 | [-1.543, +0.980] |
| PIPPINUSDT | 0 | +0.000 | — |
| PIXELUSDT | 0 | +0.000 | — |
| PNUTUSDT | 0 | +0.000 | — |
| POPCATUSDT | 0 | +0.000 | — |
| PUMPUSDT | 0 | +0.000 | — |
| QNTUSDT | 0 | +0.000 | — |
| QUSDT | 0 | +0.000 | — |
| RAREUSDT | 1 | -0.842 | — |
| REEFUSDT | 3 | +1.068 | [+0.164, +1.973] |
| RNDRUSDT | 0 | +0.000 | — |
| RSRUSDT | 1 | +0.668 | — |
| RUNEUSDT | 5 | +0.100 | [-0.681, +0.881] |
| RVNUSDT | 1 | +0.330 | — |
| SANDUSDT | 7 | -0.018 | [-0.590, +0.553] |
| SEIUSDT | 1 | -0.710 | — |
| SIRENUSDT | 0 | +0.000 | — |
| SKYAIUSDT | 0 | +0.000 | — |
| SOLUSDT | 31 | +0.248 | [-0.048, +0.545] |
| STMXUSDT | 1 | +0.551 | — |
| STORJUSDT | 1 | +0.968 | — |
| STOUSDT | 0 | +0.000 | — |
| STRKUSDT | 0 | +0.000 | — |
| STXUSDT | 0 | +0.000 | — |
| SUIUSDT | 11 | +0.180 | [-0.725, +1.085] |
| SUSHIUSDT | 3 | +0.000 | [-1.217, +1.217] |
| SXPUSDT | 3 | -0.569 | [-0.980, -0.158] |
| SYNUSDT | 0 | +0.000 | — |
| TAOUSDT | 0 | +0.000 | — |
| THETAUSDT | 2 | -0.291 | [-1.230, +0.648] |
| TIAUSDT | 4 | +0.006 | [-0.395, +0.406] |
| TLMUSDT | 0 | +0.000 | — |
| TNSRUSDT | 0 | +0.000 | — |
| TOMOUSDT | 1 | +0.340 | — |
| TONUSDT | 0 | +0.000 | — |
| TRBUSDT | 6 | +0.221 | [-0.389, +0.830] |
| TRUMPUSDT | 1 | -0.593 | — |
| TRXUSDT | 9 | +0.361 | [-0.560, +1.281] |
| TURBOUSDT | 0 | +0.000 | — |
| TUTUSDT | 0 | +0.000 | — |
| UMAUSDT | 0 | +0.000 | — |
| UNFIUSDT | 4 | -0.357 | [-0.841, +0.127] |
| UNIUSDT | 3 | -0.921 | [-1.068, -0.774] |
| UXLINKUSDT | 0 | +0.000 | — |
| VELVETUSDT | 0 | +0.000 | — |
| VETUSDT | 0 | +0.000 | — |
| VIRTUALUSDT | 0 | +0.000 | — |
| VOXELUSDT | 1 | +0.441 | — |
| WAVESUSDT | 3 | -0.084 | [-1.262, +1.095] |
| WIFUSDT | 12 | -0.004 | [-0.493, +0.484] |
| WLDUSDT | 7 | +0.070 | [-0.499, +0.640] |
| XLMUSDT | 3 | -0.128 | [-0.316, +0.060] |
| XMRUSDT | 0 | +0.000 | — |
| XPLUSDT | 0 | +0.000 | — |
| XRPUSDT | 30 | +0.230 | [-0.340, +0.800] |
| XTZUSDT | 4 | -0.223 | [-0.683, +0.237] |
| YFIIUSDT | 0 | +0.000 | — |
| YFIUSDT | 0 | +0.000 | — |
| ZECUSDT | 2 | +0.209 | [-1.874, +2.292] |
| ZILUSDT | 0 | +0.000 | — |
| ZRXUSDT | 0 | +0.000 | — |

## Holdout

No se miró: desarrollo no pasó el criterio.
