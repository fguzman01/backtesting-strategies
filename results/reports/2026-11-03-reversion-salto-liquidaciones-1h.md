# 2026-11-03-reversion-salto-liquidaciones-1h — RECHAZADA

- **Estrategia:** `reversion_salto` {"atr_n": 24, "salto_atr": 4.0, "vol_n": 24, "vol_mult": 2.0, "stop_atr": 3.0}
- **Universo:** futures · 1h · ADAUSDT, AVAXUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT
- **Evaluada:** 2026-11-03T06:42:13+00:00 · commit `6faf813`

## Hipótesis

Una vela de 1h con cuerpo ≥ 4 ATR y volumen ≥ 2× el promedio suele ser una cascada de liquidaciones apalancadas: el precio se mueve por flujo forzado, no por información, y devuelve parte del tramo en horas. Del otro lado pierden los liquidados y los que persiguen el movimiento. Mecanismo nuevo frente a la reversión rechazada (rangos/piso de canal sin condición de evento): aquí el disparador es un evento de flujo forzado, no una zona de precio. Stop ancho (3 ATR desde la entrada) justamente por la lección de la reversión (stop de 1.5 ATR cortaba las excursiones); objetivo 1R (= 3 ATR, ~75% del salto de 4 ATR). Costo: 0.1% por lado (comisión + deslizamiento alto en momentos de volatilidad); con stop de ~1-1.5% la comisión ronda 0.15-0.2R, el edge bruto debe superarlo. Se fija UNA configuración (4 ATR, 2× volumen, 3 ATR, 1R) antes de correr; no se barren umbrales. Riesgo central: evidencia C (2013-2020, resúmenes sin costos). Criterio exigente por defecto. El holdout se declara contaminado por prudencia (familia reversión ya medida en btc-signal-web con holdout visto en otros diseños): como mucho llega a observación.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 150 | 1219 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | -0.185 [-0.242, -0.129] | ❌ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 0/4 | ❌ |
| supera el percentil 95 del control nulo | -0.185 vs p95 -0.018 | ❌ |
| alcance: duración mediana ≤ 7 días | 0.2 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (-0.185 [-0.242, -0.129]); desarrollo: falla «tramos positivos ≥ 3» (0/4); desarrollo: falla «supera el percentil 95 del control nulo» (-0.185 vs p95 -0.018)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `reversion`:** 1 (esta incluida)
- **Holdout contaminado:** sí
- **Pre-registro:** commit `6faf813` del 2026-11-03T06:41:20Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -237.33 R

## Desarrollo

Ventana 2017-08-17 → 2025-09-08 · n=1219 · avgR neto -0.185 [-0.242, -0.129] · bruto -0.110 · acierto 44% · duración mediana 0.2 días

Control nulo: media -0.078, p95 -0.018

**Robustez** (informativa, no decide): costos ×1.5 → -0.224 [-0.281, -0.168] · sin las 10 mejores → -0.195 [-0.252, -0.139]

| Tramo | n | avgR neto |
|---|---|---|
| 2017-09-02 → 2019-11-15 | 305 | -0.269 |
| 2019-11-22 → 2021-10-26 | 305 | -0.116 |
| 2021-10-26 → 2023-08-02 | 305 | -0.186 |
| 2023-08-13 → 2025-09-07 | 304 | -0.171 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| ADAUSDT | 96 | -0.199 | [-0.399, +0.001] |
| AVAXUSDT | 52 | +0.096 | [-0.180, +0.372] |
| BNBUSDT | 112 | -0.211 | [-0.398, -0.024] |
| BTCUSDT | 182 | -0.372 | [-0.512, -0.233] |
| DOGEUSDT | 107 | +0.137 | [-0.052, +0.325] |
| DOTUSDT | 45 | -0.131 | [-0.420, +0.157] |
| ETHUSDT | 130 | -0.347 | [-0.513, -0.182] |
| LINKUSDT | 50 | -0.252 | [-0.532, +0.027] |
| LTCUSDT | 114 | -0.249 | [-0.432, -0.067] |
| NEARUSDT | 30 | -0.357 | [-0.705, -0.009] |
| SOLUSDT | 32 | -0.141 | [-0.494, +0.211] |
| TRXUSDT | 115 | -0.057 | [-0.243, +0.128] |
| UNIUSDT | 35 | -0.333 | [-0.659, -0.007] |
| XRPUSDT | 119 | -0.081 | [-0.264, +0.103] |

## Holdout

No se miró: desarrollo no pasó el criterio.
