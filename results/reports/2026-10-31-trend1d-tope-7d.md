# 2026-10-31-trend1d-tope-7d — RECHAZADA

- **Estrategia:** `tendencia_donchian` {"entrada": 20, "salida": 10, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 1d · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-10-31T20:44:53+00:00 · commit `f139519`

## Hipótesis

TREND_1D (Donchian 20/10, stop 2×ATR20, filtro EMA200, 14 tokens) tiene edge real: pasó desarrollo, control nulo y holdout. Pero su duración media es de 22 días, fuera del alcance de esta factory (mediana ≤ 7 días). Si buena parte del movimiento a favor ocurre en la primera semana tras la ruptura, cortar a los 7 días conserva un edge positivo y distinguible del azar.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 100 | 952 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.087 [-0.001, +0.175] | ❌ |
| supera el percentil 95 del control nulo | +0.087 vs p95 +0.080 | ✅ |
| alcance: duración mediana ≤ 7 días | 7.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (+0.087 [-0.001, +0.175])

## Desarrollo

Ventana 2020-01-01 → 2025-09-08 · n=952 · avgR neto +0.087 [-0.001, +0.175] · bruto +0.127 · acierto 44% · duración mediana 7.0 días

Control nulo: media +0.011, p95 +0.080

| Tramo | n | avgR neto |
|---|---|---|
| 2020-07-23 → 2021-11-17 | 238 | +0.208 |
| 2021-11-18 → 2023-04-14 | 238 | -0.063 |
| 2023-04-15 → 2024-07-05 | 238 | +0.157 |
| 2024-07-05 → 2025-09-02 | 238 | +0.046 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 68 | +0.127 | [-0.199, +0.453] |
| AVAXUSDT | 58 | +0.285 | [-0.092, +0.662] |
| BNBUSDT | 71 | +0.198 | [-0.160, +0.556] |
| BTCUSDT | 81 | +0.071 | [-0.179, +0.321] |
| DOGEUSDT | 59 | +0.331 | [-0.463, +1.126] |
| DOTUSDT | 61 | -0.026 | [-0.235, +0.183] |
| ETHUSDT | 80 | +0.068 | [-0.172, +0.307] |
| LINKUSDT | 78 | -0.026 | [-0.207, +0.154] |
| LTCUSDT | 73 | -0.092 | [-0.278, +0.094] |
| NEARUSDT | 58 | +0.099 | [-0.125, +0.322] |
| SOLUSDT | 60 | +0.364 | [+0.089, +0.640] |
| TRXUSDT | 75 | -0.122 | [-0.326, +0.081] |
| UNIUSDT | 62 | -0.194 | [-0.383, -0.005] |
| XRPUSDT | 68 | +0.250 | [-0.221, +0.721] |

## Holdout

No se miró: desarrollo no pasó el criterio.
