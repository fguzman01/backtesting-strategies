# 2026-11-13-trend4h-t7-vs-madre — NO_CONCLUYENTE

- **Estrategia:** `tendencia_donchian` {"entrada": 20, "salida": 10, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 4h · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-11-13T10:27:03+00:00 · commit `3713568`

## Hipótesis

Pregunta de medición, no una estrategia nueva. TREND_4H_T7 (`2026-11-02-trend4h-tope-7d`, hoy en observación) es variante de TREND_4H sin tope, y su ficha en `approved.json` tiene `comparacion_madre: null`. Esta spec corre la MISMA regla (20/10/20/200/2.0), los mismos 14 tokens, costos, cupo (ninguno) y ventana de desarrollo que la original; la hija usa timeout de 42 velas (7 d) y la madre el mayor tope que el alcance permite (84 velas = 14 d), porque `timeout_velas: null` no pasa la validación (alcance.md: trades de como mucho 14 días). La madre es entonces «sin tope efectivo de 7 d», no una tendencia sin tope: la salida por canal de 10 velas (~40 h) y el stop suelen cerrar antes. Se fija UNA comparación antes de correr; no se barren topes. Mide SÓLO el período de desarrollo (`solo_desarrollo: true`): el holdout de la familia tendencia ya se miró 3 veces y no se vuelve a mirar, ni para la hija ni para la madre. El veredicto de la spec (NO_CONCLUYENTE por diseño) importa menos que la diferencia; no va a `approved.json`. Interpretación fijada de antemano: si hija − madre + 2 EE < 0, el tope le quita edge a T7; si hija − madre − 2 EE > 0, el tope agrega; si el intervalo incluye 0, el tope no cambia nada medible. Las muestras se solapan, así que el ±2 EE es una guía conservadora, no un test formal.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 4631 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.245 [+0.178, +0.312] | ✅ |
| avgR neto > 0 | +0.245 | ✅ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 4/4 | ✅ |
| supera el percentil 95 del control nulo | +0.245 vs p95 +0.033 | ✅ |
| alcance: duración mediana ≤ 7 días | 3.0 días | ✅ |

**Motivos:** holdout no mirado (solo_desarrollo): sin holdout no hay veredicto de aprobación

## Ficha

- **Nivel:** —
- **Pruebas en la familia `tendencia`:** 11 (esta incluida; 4 medidas fuera de este repo)
  - `2026-10-31-trend1d-tope-7d`: RECHAZADA, desarrollo +0.087
  - `2026-11-01-trend1d-chandelier-14d`: RECHAZADA, desarrollo +0.148
  - `2026-11-02-trend4h-tope-7d`: APROBADA, desarrollo +0.245, holdout mirado
  - `2026-11-04-trend1d-trailing-atr-real-14d`: RECHAZADA, desarrollo +0.049
  - `2026-11-04-trend4h-t7-control-14`: OBSERVACION, desarrollo +0.189, holdout mirado
  - `2026-11-04-trend4h-t7-universo-dinamico`: OBSERVACION, desarrollo +0.126, holdout mirado
- **Holdout contaminado:** sí
- **Pre-registro:** commit `3713568` del 2026-11-13T07:26:14-03:00
- **Cupo de cartera:** sin cupo
- **Peor caída (desarrollo):** -73.45 R
- **Contra la madre `TREND_4H sin tope (14 d)` (desarrollo):** hija +0.245 (n=4631) vs madre +0.273 (n=4304) → diferencia -0.028 [-0.137, +0.081]; peor caída -73.45 vs -80.06 R

## Estabilidad de parámetros

Misma spec en desarrollo con todos los parámetros numéricos movidos a la vez. Si sólo funciona con los números exactos, es sobreajuste.

| Parámetros | n | avgR neto | ±2 EE | Conserva |
|---|---|---|---|---|
| como se pre-registraron | 4631 | +0.245 | [+0.178, +0.312] | 100% |
| ×0.8 {"entrada": 16, "salida": 8, "atr_n": 16, "ema_n": 160, "stop_atr": 1.6} | 5625 | +0.224 | [+0.155, +0.292] | 91% |
| ×1.2 {"entrada": 24, "salida": 12, "atr_n": 24, "ema_n": 240, "stop_atr": 2.4} | 4036 | +0.220 | [+0.156, +0.284] | 90% |

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

No se miró: desarrollo no pasó el criterio.
