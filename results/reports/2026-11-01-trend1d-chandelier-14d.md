# 2026-11-01-trend1d-chandelier-14d — RECHAZADA

- **Estrategia:** `tendencia_chandelier` {"entrada": 20, "salida_n": 22, "salida_atr": 3.0, "atr_n": 20, "ema_n": 200, "stop_atr": 2.0}
- **Universo:** futures · 1d · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-11-01T06:41:13+00:00 · commit `8ba1697`

## Hipótesis

El edge de TREND_1D vive en pocas tendencias largas, que el tope fijo de 7 días cortaba. Un trailing chandelier (máximo de 22 velas − 3 ATR) saca las operaciones que pierden momentum pronto pero deja correr las que siguen dando máximos, hasta el tope de 14 días permitido por el alcance. La entrada y el stop inicial son los de TREND_1D, así que la diferencia es sólo la salida: si el edge sobrevive, es porque capturar el tramo 7–14 días de las buenas tendencias compensa la comisión (0.1% por lado ≈ 0.05R con stop de 2 ATR de ~4%). Se elige UNA configuración (22 / 3.0) antes de correr; no se barren parámetros. Criterio exigente por defecto.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 100 | 814 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.148 [+0.022, +0.274] | ✅ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2020-07-23:+0.51R 2022-01-06:-0.15R 2023-05-09:+0.14R 2024-07-16:+0.09R): depende del régimen; la dispersión entre tramos (0.67R) supera el doble del avgR (0.148R) | ❌ |
| tramos positivos ≥ 3 | 3/4 | ✅ |
| supera el percentil 95 del control nulo | +0.148 vs p95 +0.121 | ✅ |
| alcance: duración mediana ≤ 7 días | 14.0 días | ❌ |

**Motivos:** desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-07-23:+0.51R 2022-01-06:-0.15R 2023-05-09:+0.14R 2024-07-16:+0.09R): depende del régimen; la dispersión entre tramos (0.67R) supera el doble del avgR (0.148R)); desarrollo: falla «alcance: duración mediana ≤ 7 días» (14.0 días)

## Desarrollo

Ventana 2020-01-01 → 2025-09-08 · n=814 · avgR neto +0.148 [+0.022, +0.274] · bruto +0.197 · acierto 41% · duración mediana 14.0 días

Control nulo: media +0.019, p95 +0.121

| Tramo | n | avgR neto |
|---|---|---|
| 2020-07-23 → 2021-12-24 | 204 | +0.515 |
| 2022-01-06 → 2023-05-09 | 204 | -0.154 |
| 2023-05-09 → 2024-07-16 | 203 | +0.144 |
| 2024-07-16 → 2025-09-02 | 203 | +0.086 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 55 | +0.451 | [-0.098, +1.001] |
| AVAXUSDT | 50 | +0.211 | [-0.279, +0.700] |
| BNBUSDT | 62 | +0.169 | [-0.333, +0.671] |
| BTCUSDT | 68 | +0.208 | [-0.163, +0.579] |
| DOGEUSDT | 55 | +0.414 | [-0.545, +1.372] |
| DOTUSDT | 55 | -0.162 | [-0.395, +0.071] |
| ETHUSDT | 67 | +0.201 | [-0.212, +0.615] |
| LINKUSDT | 64 | +0.109 | [-0.205, +0.422] |
| LTCUSDT | 64 | -0.110 | [-0.392, +0.173] |
| NEARUSDT | 50 | +0.116 | [-0.179, +0.411] |
| SOLUSDT | 51 | +0.333 | [-0.088, +0.754] |
| TRXUSDT | 63 | -0.113 | [-0.407, +0.181] |
| UNIUSDT | 53 | -0.103 | [-0.463, +0.257] |
| XRPUSDT | 57 | +0.402 | [-0.297, +1.101] |

## Holdout

No se miró: desarrollo no pasó el criterio.
