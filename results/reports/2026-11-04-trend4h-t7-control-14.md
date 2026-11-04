# 2026-11-04-trend4h-t7-control-14 — OBSERVACION

- **Estrategia:** `tendencia_donchian` {"entrada": 20, "salida": 10, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 4h · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-11-04T19:10:04+00:00 · commit `3dcd294`

**Sólo medición:** Pregunta de medición (backlog B-05), no una estrategia para operar: no va a approved.json. Marcada el 2026-11-04 porque la spec es anterior al campo `medicion: true`.

## Hipótesis

Pregunta de medición, no una estrategia nueva (backlog B-05): cuánto del edge de `2026-11-02-trend4h-tope-7d` (TREND_4H_T7, en paper en btc-signal-web) es sesgo de supervivencia. Se aprobó (hoy en observación) midiendo sólo los 14 tokens que siguen vivos. Este par de specs corre la MISMA regla, parámetros, costos y tope en la MISMA ventana (desde 2020-04, primer mes de la tabla del universo, sin historia de spot): `una con el universo de cada spec; la otra usa el universo dinámico (2026-11-04-trend4h-t7-universo-dinamico)`. La diferencia entre los dos avgR de desarrollo es lo que aportaba elegir sobrevivientes. Sin cupo, igual que la evaluación original, para cambiar una sola cosa. Criterio exigente por defecto (como toda spec nueva); el veredicto de cada una importa menos que la comparación. Holdout contaminado: ya se miró al aprobarla. Esta es el control: los 14 tokens fijos de la evaluación original, en la ventana corta.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 3831 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.189 [+0.116, +0.261] | ✅ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 4/4 | ✅ |
| supera el percentil 95 del control nulo | +0.189 vs p95 +0.040 | ✅ |
| alcance: duración mediana ≤ 7 días | 3.0 días | ✅ |
| holdout: hay operaciones | n=919 | ✅ |
| holdout: avgR neto > 0 | +0.033 (n=919) | ✅ |
| holdout: con costos ×1.5 avgR > 0 | +0.002 | ✅ |
| holdout: sin las 10 mejores avgR ≥ 0 | -0.097 | ❌ |
| holdout: conserva ≥ 33% del avgR de desarrollo | +0.033 vs mínimo +0.062 | ❌ |

**Motivos:** holdout: sin las 10 mejores avgR ≥ 0 (-0.097); holdout: conserva ≥ 33% del avgR de desarrollo (+0.033 vs mínimo +0.062); holdout contaminado: ese período ya se miró con una estrategia emparentada

## Ficha

- **Nivel:** observacion
- **Pruebas en la familia `tendencia`:** 9 (esta incluida; 4 medidas fuera de este repo)
  - `2026-10-31-trend1d-tope-7d`: RECHAZADA, desarrollo +0.087
  - `2026-11-01-trend1d-chandelier-14d`: RECHAZADA, desarrollo +0.148
  - `2026-11-02-trend4h-tope-7d`: APROBADA, desarrollo +0.245, holdout mirado
  - `2026-11-04-trend1d-trailing-atr-real-14d`: RECHAZADA, desarrollo +0.049
- **Holdout contaminado:** sí
- **Pre-registro:** commit `83f0bc7` del 2026-11-04T18:51:09Z
- **Cupo de cartera:** sin cupo
- **Peor caída (desarrollo):** -73.45 R
- **Peor caída (holdout):** -128.50 R

## Estabilidad de parámetros

Misma spec en desarrollo con todos los parámetros numéricos movidos a la vez. Si sólo funciona con los números exactos, es sobreajuste.

| Parámetros | n | avgR neto | ±2 EE | Conserva |
|---|---|---|---|---|
| como se pre-registraron | 3831 | +0.189 | [+0.116, +0.261] | 100% |
| ×0.8 {"entrada": 16, "salida": 8, "atr_n": 16, "ema_n": 160, "stop_atr": 1.6} | 4621 | +0.172 | [+0.098, +0.246] | 91% |
| ×1.2 {"entrada": 24, "salida": 12, "atr_n": 24, "ema_n": 240, "stop_atr": 2.4} | 3337 | +0.169 | [+0.098, +0.239] | 89% |

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=3831 · avgR neto +0.189 [+0.116, +0.261] · bruto +0.257 · acierto 34% · duración mediana 3.0 días

Control nulo: media -0.026, p95 +0.040

**Robustez** (informativa, no decide): costos ×1.5 → +0.166 [+0.093, +0.239] · sin las 10 mejores → +0.129 [+0.069, +0.190]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-06 → 2021-10-14 | 958 | +0.342 |
| 2021-10-15 → 2023-02-14 | 958 | +0.116 |
| 2023-02-15 → 2024-06-14 | 958 | +0.163 |
| 2024-06-14 → 2025-09-08 | 957 | +0.133 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 293 | +0.219 | [-0.054, +0.492] |
| AVAXUSDT | 266 | +0.214 | [-0.026, +0.454] |
| BNBUSDT | 286 | +0.183 | [-0.086, +0.452] |
| BTCUSDT | 279 | +0.190 | [-0.094, +0.473] |
| DOGEUSDT | 251 | +0.628 | [+0.053, +1.203] |
| DOTUSDT | 256 | +0.153 | [-0.052, +0.357] |
| ETHUSDT | 288 | +0.217 | [-0.031, +0.466] |
| LINKUSDT | 285 | +0.115 | [-0.101, +0.332] |
| LTCUSDT | 286 | +0.057 | [-0.157, +0.271] |
| NEARUSDT | 249 | +0.196 | [-0.016, +0.408] |
| SOLUSDT | 261 | +0.248 | [+0.015, +0.480] |
| TRXUSDT | 296 | +0.104 | [-0.140, +0.348] |
| UNIUSDT | 260 | +0.082 | [-0.110, +0.274] |
| XRPUSDT | 275 | +0.080 | [-0.167, +0.327] |

## Holdout

Ventana 2025-09-09 → 2026-11-03 · n=919 · avgR neto +0.033 [-0.096, +0.163] · bruto +0.108 · acierto 32% · duración mediana 2.5 días

Control nulo: media -0.043, p95 +0.049

**Robustez** (informativa, no decide): costos ×1.5 → +0.002 [-0.127, +0.131] · sin las 10 mejores → -0.097 [-0.195, +0.000]

| Tramo | n | avgR neto |
|---|---|---|
| 2025-09-09 → 2025-12-25 | 230 | +0.115 |
| 2025-12-28 → 2026-04-12 | 230 | -0.066 |
| 2026-04-12 → 2026-07-21 | 230 | -0.055 |
| 2026-07-21 → 2026-11-02 | 229 | +0.140 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 65 | +0.187 | [-0.262, +0.636] |
| AVAXUSDT | 64 | -0.036 | [-0.454, +0.383] |
| BNBUSDT | 62 | +0.040 | [-0.437, +0.516] |
| BTCUSDT | 66 | +0.149 | [-0.491, +0.788] |
| DOGEUSDT | 57 | +0.069 | [-0.410, +0.547] |
| DOTUSDT | 66 | -0.128 | [-0.406, +0.151] |
| ETHUSDT | 62 | +0.279 | [-0.444, +1.001] |
| LINKUSDT | 69 | -0.155 | [-0.537, +0.228] |
| LTCUSDT | 67 | -0.102 | [-0.472, +0.268] |
| NEARUSDT | 68 | +0.178 | [-0.350, +0.706] |
| SOLUSDT | 64 | +0.194 | [-0.395, +0.782] |
| TRXUSDT | 74 | -0.267 | [-0.577, +0.044] |
| UNIUSDT | 67 | +0.005 | [-0.394, +0.404] |
| XRPUSDT | 68 | +0.119 | [-0.479, +0.717] |
