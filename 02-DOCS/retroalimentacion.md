# Retroalimentación del bot

Lo que vuelve de btc-signal-web: el paper de cada aprobada contra lo que predijo la factory, una vez
por semana (agente Puente, `.claude/agents/puente.md`; datos de `bt.puente`). Una línea marcada
⚠️ PEOR es una alerta para el auditor, no un veredicto: con muestra suficiente, el holdout del
backtest quedó por encima del intervalo de ±2 EE del paper.

Además se anotan acá los issues `retro` de la factory (comentarios del bot sobre una ficha o una
aprobada) y qué se hizo con cada uno.

## Informe del 2026-11-07 (PROD, commit 1c0d294)

| Estrategia | Nivel | Paper n | Paper avgR ±2 EE | Holdout backtest | Lectura | Madre en la misma ventana |
|---|---|---|---|---|---|---|
| `2026-11-02-trend4h-tope-7d` → TREND_4H_T7 | observacion | 5 (+3 abiertas) | -0.896 [-1.202, -0.589] | +0.036 (n=916) | muestra chica: no se concluye | TREND_4H: n=3 -1.052; diferencia +0.156 [-0.151, +0.464] |
