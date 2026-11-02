# 2026-11-02-trend4h-tope-7d — APROBADA

- **Estrategia:** `tendencia_donchian` {"entrada": 20, "salida": 10, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 4h · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-11-02T06:42:42+00:00 · commit `95e24ef`

## Hipótesis

Las rupturas de canal con filtro de tendencia capturan la incorporación lenta de información y la persecución de los rezagados. En 4h una tendencia madura en horas o pocos días, no semanas: el canal de salida de 10 velas (~40 h) y el tope de 7 días (42 velas) deberían cortar las operaciones sin sacrificar la parte del movimiento donde está el edge (en TREND_1D el tope de 7 d se comía el edge porque la tendencia diaria tarda ~22 días). Hay más operaciones y más cortas. Costo: 0.1% por lado (comisión 0.05% + deslizamiento 0.05%); con stop de 2 ATR(4h) de ~2-3% la comisión ronda 0.07-0.10R por operación. Es el costo central: el edge bruto debe superarlo con holgura. Se fija UNA configuración (20/10/20/200/2.0, la misma regla que TREND_1D llevada a 4h sin reoptimizar) antes de correr; no se barren parámetros. Criterio exigente por defecto. Esta evaluación decide el cierre de la familia de tendencia en la factory (alcance.md, 2026-11-01).

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 4631 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.245 [+0.178, +0.312] | ✅ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 4/4 | ✅ |
| supera el percentil 95 del control nulo | +0.245 vs p95 +0.033 | ✅ |
| alcance: duración mediana ≤ 7 días | 3.0 días | ✅ |
| holdout: avgR neto > 0 | +0.036 (n=916) | ✅ |

**Reclasificada 2026-11-02: aprobada → observacion.** Reclasificada el 2026-11-02 por la retroalimentación de btc-signal-web, antes de existir los dos niveles: el holdout es positivo pero débil (+0.036, IC [−0.094, +0.166]; sin las 10 mejores −0.095; con costos ×1.5 +0.004; conserva 15% del avgR de desarrollo, el mínimo nuevo es 33%) y está contaminado (btc-signal-web ya había mirado ese período con TREND_4H sin tope). El veredicto registrado no se cambia; cambia el nivel.

## Ficha

- **Nivel:** observacion
- **Pruebas en la familia `tendencia`:** 3 (esta incluida)
  - `2026-10-31-trend1d-tope-7d`: RECHAZADA, desarrollo +0.087
  - `2026-11-01-trend1d-chandelier-14d`: RECHAZADA, desarrollo +0.148
- **Holdout contaminado:** sí
- **Pre-registro:** commit `95e24ef` del 2026-11-02T06:41:08+00:00
- **Cupo de cartera:** sin cupo
- **Peor caída (desarrollo):** -73.24 R
- **Peor caída (holdout):** -122.78 R

## Desarrollo

Ventana 2017-08-17 → 2025-09-08 · n=4631 · avgR neto +0.245 [+0.178, +0.312] · bruto +0.310 · acierto 35% · duración mediana 3.0 días

Control nulo: media -0.033, p95 +0.033

**Robustez** (informativa, no decide): costos ×1.5 → +0.222 [+0.156, +0.289] · sin las 10 mejores → +0.195 [+0.137, +0.252]

| Tramo | n | avgR neto |
|---|---|---|
| 2017-09-21 → 2020-12-13 | 1158 | +0.434 |
| 2020-12-13 → 2022-07-28 | 1158 | +0.286 |
| 2022-07-28 → 2024-03-04 | 1158 | +0.152 |
| 2024-03-05 → 2025-09-08 | 1157 | +0.107 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 380 | +0.271 | [+0.038, +0.503] |
| AVAXUSDT | 266 | +0.214 | [-0.026, +0.454] |
| BNBUSDT | 397 | +0.325 | [+0.089, +0.561] |
| BTCUSDT | 399 | +0.339 | [+0.094, +0.584] |
| DOGEUSDT | 287 | +0.676 | [+0.150, +1.202] |
| DOTUSDT | 257 | +0.150 | [-0.053, +0.354] |
| ETHUSDT | 404 | +0.329 | [+0.111, +0.546] |
| LINKUSDT | 342 | +0.132 | [-0.070, +0.334] |
| LTCUSDT | 386 | +0.136 | [-0.052, +0.323] |
| NEARUSDT | 250 | +0.191 | [-0.020, +0.402] |
| SOLUSDT | 265 | +0.253 | [+0.023, +0.483] |
| TRXUSDT | 384 | +0.146 | [-0.068, +0.360] |
| UNIUSDT | 259 | +0.083 | [-0.109, +0.275] |
| XRPUSDT | 355 | +0.153 | [-0.071, +0.377] |

## Holdout

Ventana 2025-09-09 → 2026-10-31 · n=916 · avgR neto +0.036 [-0.094, +0.166] · bruto +0.111 · acierto 32% · duración mediana 2.5 días

Control nulo: media -0.045, p95 +0.043

**Robustez** (informativa, no decide): costos ×1.5 → +0.004 [-0.125, +0.134] · sin las 10 mejores → -0.095 [-0.193, +0.003]

| Tramo | n | avgR neto |
|---|---|---|
| 2025-09-09 → 2025-12-24 | 229 | +0.120 |
| 2025-12-25 → 2026-04-11 | 229 | -0.064 |
| 2026-04-12 → 2026-07-20 | 229 | -0.057 |
| 2026-07-20 → 2026-10-31 | 229 | +0.145 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 64 | +0.195 | [-0.261, +0.651] |
| AVAXUSDT | 64 | -0.036 | [-0.454, +0.383] |
| BNBUSDT | 62 | +0.046 | [-0.430, +0.522] |
| BTCUSDT | 66 | +0.155 | [-0.484, +0.794] |
| DOGEUSDT | 57 | +0.066 | [-0.412, +0.545] |
| DOTUSDT | 66 | -0.128 | [-0.406, +0.151] |
| ETHUSDT | 62 | +0.290 | [-0.432, +1.011] |
| LINKUSDT | 69 | -0.155 | [-0.537, +0.228] |
| LTCUSDT | 66 | -0.096 | [-0.472, +0.279] |
| NEARUSDT | 67 | +0.172 | [-0.364, +0.708] |
| SOLUSDT | 64 | +0.183 | [-0.406, +0.771] |
| TRXUSDT | 74 | -0.250 | [-0.565, +0.066] |
| UNIUSDT | 67 | +0.005 | [-0.394, +0.404] |
| XRPUSDT | 68 | +0.122 | [-0.476, +0.720] |
