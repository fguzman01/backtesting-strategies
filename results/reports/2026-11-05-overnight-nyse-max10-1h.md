# 2026-11-05-overnight-nyse-max10-1h — NO_CONCLUYENTE

- **Estrategia:** `overnight_max` {"max_dias": 10, "atr_n": 24, "stop_atr": 6.0, "hora_entrada": 16, "hora_salida": 10}
- **Universo:** futures · 1h · BTCUSDT
- **Evaluada:** 2026-11-05T06:41:22+00:00 · commit `a9f8907`

## Hipótesis

La subida de BTC se concentraría fuera del horario bursátil de EE. UU. (flujos de sesión y liquidez); el filtro de máximo de 10 días agrega inercia (momentum de corto plazo) a esa deriva nocturna. Del otro lado pierde quien vende contra la inercia en una noche sin la contraparte bursátil. Costo: 0.1% por lado (comisión + deslizamiento) contra una operación de ~18 h con stop de 6 ATR de 1h (~3%): ~0.07R de comisión, que el edge bruto debe superar. UNA regla fija antes de correr, sin barrer parámetros: entrada en la apertura de las 16:00 ET (tras la vela que cierra a las 16:00 ET), cierre ≥ máximo de los cierres de las 240 velas previas (10 días), sólo largo, salida por regla en la apertura de las 10:00 ET siguiente, todos los días (cripto no cierra los fines de semana), horario de EE. UU. con cambio de hora (America/New_York). Stop 6 ATR(24) de 1h como protección de cola (no es parte del mecanismo). El 10 viene del trabajo de origen, no se optimizó acá. Universo: sólo BTCUSDT porque la evidencia de origen es de BTC y la pregunta es sobre ese mecanismo (con spot desde 2017 para tener varios regímenes, incluido el bajista de 2018); no es una lista de supervivientes que compre alts. Riesgo central: evidencia C (sin costos en la fuente, corte fuera de muestra elegido a dedo, una sola operación por noche). Criterio exigente por defecto con corrección por pruebas. Holdout declarado contaminado por prudencia: la estacionalidad por hora ya se midió en btc-signal-web sobre un período que cruza el holdout de este repo; como mucho llega a observación.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 150 | 105 | ❌ |
| avgR neto > 0 y ±2 EE fuera del cero | +0.007 [-0.105, +0.119] | ❌ |
| ajustado por 4 prueba(s) de la familia: avgR − 2.50 EE > 0 | +0.007 − 2.50×0.056 = -0.133 | ❌ |
| concluyente (muestra, modelos, tramos) | los tramos no coinciden en signo (2017-09-01:-0.12R 2019-05-13:-0.05R 2021-10-01:+0.22R 2023-12-08:-0.02R): depende del régimen; la dispersión entre tramos (0.35R) supera el doble del avgR (0.007R) | ❌ |
| tramos positivos ≥ 3 | 1/4 | ❌ |
| supera el percentil 95 del control nulo | +0.007 vs p95 +0.094 | ❌ |
| alcance: duración mediana ≤ 7 días | 0.8 días | ✅ |

**Motivos:** desarrollo: falla «n ≥ 150» (105); desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (+0.007 [-0.105, +0.119]); desarrollo: falla «ajustado por 4 prueba(s) de la familia: avgR − 2.50 EE > 0» (+0.007 − 2.50×0.056 = -0.133); desarrollo: falla «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2017-09-01:-0.12R 2019-05-13:-0.05R 2021-10-01:+0.22R 2023-12-08:-0.02R): depende del régimen; la dispersión entre tramos (0.35R) supera el doble del avgR (0.007R)); desarrollo: falla «tramos positivos ≥ 3» (1/4); desarrollo: falla «supera el percentil 95 del control nulo» (+0.007 vs p95 +0.094)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `estacionalidad`:** 4 (esta incluida; 3 medidas fuera de este repo)
- **Holdout contaminado:** sí
- **Pre-registro:** commit `a9f8907` del 2026-11-05T06:40:51Z
- **Cupo de cartera:** máx 1 por dirección
- **Peor caída (desarrollo):** -5.84 R

## Desarrollo

Ventana 2017-08-17 → 2025-09-08 · n=105 · avgR neto +0.007 [-0.105, +0.119] · bruto +0.052 · acierto 47% · duración mediana 0.8 días

Control nulo: media -0.017, p95 +0.094

**Robustez** (informativa, no decide): costos ×1.5 → -0.013 [-0.126, +0.099] · sin las 10 mejores → -0.108 [-0.203, -0.013]

| Tramo | n | avgR neto |
|---|---|---|
| 2017-09-01 → 2019-05-09 | 27 | -0.123 |
| 2019-05-13 → 2021-08-07 | 26 | -0.053 |
| 2021-10-01 → 2023-12-02 | 26 | +0.224 |
| 2023-12-08 → 2025-08-13 | 26 | -0.017 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| BTCUSDT | 105 | +0.007 | [-0.105, +0.119] |

## Holdout

No se miró: desarrollo no pasó el criterio.
