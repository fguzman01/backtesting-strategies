# Preguntas ya cerradas

**Antes de proponer evaluar una estrategia, parámetro o activo, buscá acá.** Indexado por la
pregunta. Una línea por pregunta; el detalle va en el commit o en el reporte.

Origen: resumen de `fguzman01/btc-signal-web/DECISIONES.md` al 2026-10-31. Ese archivo sigue
siendo la fuente con todos los números; si hay duda, leer la fila original.

> ⚠️ Los avgR de btc-signal-web medidos **antes del 2026-10-11** son optimistas (compuerta y
> llenado usaban el mismo parámetro). Re-medir antes de citar.

## Estrategias (medidas en btc-signal-web)

| Pregunta | Veredicto | Cuándo |
|---|---|---|
| ¿Momentum relativo cross-sectional (largo top-3 / corto bottom-3, rebalanceo semanal)? | **No.** Desarrollo +1.0%/semana, holdout −0.56% y 1/4 tramos. Rechazado contra criterio pre-registrado | 2026-10-11 |
| ¿Motor de tendencia en 1h (escala 15m→30m→1h)? | **Sí.** Mejora monótona con la temporalidad; 1h desarrollo +0.188 (n=1323), holdout +0.157 (n=417), 4/5 positivos | 2026-10-11 |
| ¿Reversión a la media / rangos / comprar piso de canal, con stop? | **No.** 5 diseños × 2 temporalidades, todos negativos antes de comisiones. El precio vuelve, pero tras excursiones que un stop de 1.5 ATR corta | 2026-08-31 |
| ¿Oro (XAU/PAXG) con estrategias intradía? | **No.** Edge bruto +0.08R contra comisión 0.15R | 2026-09-28 |
| ¿Oro en diario (SWING_1D)? | **Sí, en producción.** Re-medido con modelo corregido: desarrollo +0.102 n=35, tramos −−++, el intervalo toca el cero | 2026-09-29 / 10-11 |
| ¿TREND_1D (Donchian 20/10 sin techo) en oro? | **No.** Desarrollo +0.022 ±0.51 n=37; entradas al azar rinden más. Holdout no mirado | 2026-10-24 |
| ¿Motor diario sobre velas de 4h (punto medio)? | **No.** 0 de 16 tramos positivos; edge bruto ya negativo | 2026-09-29 |
| ¿Sesiones en oro (ruptura rango asiático en apertura de Londres)? | **No.** Ninguna ventana distinguible de cero | 2026-09-29 |
| ¿SCALP_5M_PULLBACK (5m o 15m)? | **No, retirada.** Holdout BTC 5m −0.233 ±0.056 | 2026-09-30 |
| ¿SCALP_5M_BREAKOUT (5m o 15m)? | **No, retirada.** 12 configuraciones, ninguna con intervalo fuera del cero | 2026-09-30 |
| ¿SCALP_15M en qué símbolos? | 8 de 14 pasan (UNI, ADA, DOGE, NEAR, AVAX, XRP, LINK, ETH). No: BTC, SOL, BNB, TRX, DOT, LTC | 2026-09-30 |
| ¿Por qué SCALP_15M rinde peor en vivo que en backtest? | **Abierta.** Vivo −0.389 ±0.313 (n=30) vs backtest +0.151. Deslizamiento explica sólo parte | 2026-10-11 |
| ¿Exigir más tendencia (ADX 4h ≥ 25) en SCALP_1H? | **No.** Ni el puntaje más alto muestra edge | 2026-10-18 |

## Parámetros (medidos en btc-signal-web)

| Pregunta | Veredicto | Cuándo |
|---|---|---|
| ¿Cerrar 100% en TP1 o parcial + breakeven + TP2? | **100% en TP1.** El parcial pierde en 12 de 14 series | 2026-09-17 / 10-01 |
| ¿TP1 más ambicioso que 1R? | **1.5R en 15m/30m**, validado fuera de muestra (21 de 22 series). No en 5m | 2026-10-02 |
| ¿Abrir el techo (TP2 > 2R o trailing)? | **No.** Plano entre 2R y 3R, empeora más allá | 2026-10-11 |
| ¿Timeout? | 480 min en 5m/15m/30m. "Sin límite" bloquea posiciones y desploma n | 2026-10-01 |
| ¿Cooldowns tras SL cambian el backtest? | **No.** −0.0001R de delta medio | 2026-10-11 |
| ¿Guarda de R:R mínimo? | **No.** Empeora la muestra | 2026-09-22 |
| ¿Relajar o acelerar la compuerta de tendencia 4h (EMA200→EMA100/50)? | **No** en ambos sentidos | 2026-09-17 / 10-08 |

## Aprendizajes estructurales

- La frontera que decide es **comisión / stop**, no la temporalidad: stops más anchos (marcos
  mayores) pagan mucho menos comisión en R.
- Las estrategias de btc-signal-web son **seguimiento de tendencia calibrado en cripto**; no
  transfieren a oro intradía.
- Varias estrategias dependen del **régimen** más de lo que rinden: siempre mirar tramos.

## Medidas en este repo

| Pregunta | Veredicto | Cuándo | Reporte |
|---|---|---|---|
| ¿El motor de este repo reproduce los resultados de btc-signal-web? | **Sí, para TREND_1D.** 14 tokens desarrollo n=568 +0.541 (registrado n=567 +0.545); holdout n=107 +0.258 (107, +0.256); oro desarrollo n=37 +0.029 (37, +0.022). Paridad exacta operación por operación con el script original en datos sintéticos. Pendiente: estrategias de scalp/swing intradía (motor TS) | 2026-10-31 | `validacion.yml`, run 41233661837 |
| ¿TREND_1D sigue teniendo edge si se corta a los 7 días (para entrar en el alcance)? (`2026-10-31-trend1d-tope-7d`) | **RECHAZADA, por muy poco.** Desarrollo 2020-07→2025-09, 14 tokens, n=952, **+0.087 [−0.001, +0.175]**: el intervalo toca el cero por una milésima. Sí le gana al azar (nulo p95 +0.080) y 3/4 tramos positivos. Sin tope era +0.545: el tope se come la mayor parte del edge, que vive en pocas tendencias largas. Holdout NO mirado | 2026-10-31 | `results/reports/2026-10-31-trend1d-tope-7d.md` |
