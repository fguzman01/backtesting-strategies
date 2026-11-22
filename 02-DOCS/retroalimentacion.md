# Retroalimentación del bot

Lo que vuelve de btc-signal-web: el paper de cada aprobada contra lo que predijo la factory, una vez
por semana (agente Puente, `.claude/agents/puente.md`; datos de `bt.puente`). Una línea marcada
⚠️ PEOR es una alerta para el auditor, no un veredicto: con muestra suficiente, el holdout del
backtest quedó por encima del intervalo de ±2 EE del paper.

Además se anotan acá los issues `retro` de la factory (comentarios del bot sobre una ficha o una
aprobada) y qué se hizo con cada uno.

## Informe del 2026-11-21 (PROD, commit d8d6c39)

| Estrategia | Nivel | Paper n | Paper avgR ±2 EE | Holdout backtest | Lectura | Madre en la misma ventana |
|---|---|---|---|---|---|---|
| `2026-11-02-trend4h-tope-7d` → TREND_4H_T7 | observacion | 11 (+3 abiertas) | +0.721 [-0.627, +2.069] | +0.036 (n=916) | muestra chica: no se concluye | TREND_4H: n=7 +0.236; diferencia +0.484 [-1.510, +2.479] |

Issues `retro` abiertos al 2026-11-22: ninguno. Lectura: el avgR de T7 en paper pasó de −0.896 (n=5, 11-07) a −0.441 (n=8, 11-14) a +0.721 (n=11, 11-21), con ±2 EE de ±1.3R: es ruido de muestra chica, no una señal en ningún sentido. Ningún umbral de T7 se cumple (11 de 60 cerradas, 20 días de 3 meses).

## Informe del 2026-11-14 (PROD, commit fd8aa7a)

| Estrategia | Nivel | Paper n | Paper avgR ±2 EE | Holdout backtest | Lectura | Madre en la misma ventana |
|---|---|---|---|---|---|---|
| `2026-11-02-trend4h-tope-7d` → TREND_4H_T7 | observacion | 8 (+3 abiertas) | -0.441 [-1.199, +0.318] | +0.036 (n=916) | muestra chica: no se concluye | TREND_4H: n=5 -0.844; diferencia +0.403 [-0.456, +1.262] |

## Informe del 2026-11-07 (PROD, commit 1c0d294)

| Estrategia | Nivel | Paper n | Paper avgR ±2 EE | Holdout backtest | Lectura | Madre en la misma ventana |
|---|---|---|---|---|---|---|
| `2026-11-02-trend4h-tope-7d` → TREND_4H_T7 | observacion | 5 (+3 abiertas) | -0.896 [-1.202, -0.589] | +0.036 (n=916) | muestra chica: no se concluye | TREND_4H: n=3 -1.052; diferencia +0.156 [-0.151, +0.464] |
