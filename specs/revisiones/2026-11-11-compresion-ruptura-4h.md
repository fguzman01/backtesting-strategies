veredicto: observaciones
2026-11-11-compresion-ruptura-4h

- No encontré look-ahead en `compresion_ruptura.py`. La caja usa `.shift(1)`, el percentil usa `ancho.shift(1).rolling(...)` (la vela no entra en su propia referencia), no hay índices hacia adelante y `rolling` no está centrado. El test llama a `chequear_lookahead` con los PARAMS exactos de la spec. Los tests no los pude correr: falta `numpy` en el entorno (`ModuleNotFoundError`). Hay que confirmarlos en el CI.
- Repetición: en `decisiones.md` no hay ninguna pregunta sobre compresión de volatilidad. El mecanismo (la compresión previa como condición) es nuevo frente a SCALP_5M_BREAKOUT, SWING_1D y la ruptura del rango asiático en oro. No es un parámetro afinado.
- Snooping: hay una sola configuración, la misma que la idea #12 de `ideas.md`, fijada antes de correr. No sale de ninguna corrida previa. La evidencia de la regla es D, solo de vendors.
- Criterio: es más exigente que `PLANTILLA.yaml` (`n_minimo` 300 contra 100). Los demás controles están activos, holdout estricto incluido.
- Holdout contaminado (el riesgo principal): `holdout_contaminado: false` se justifica diciendo que TREND_4H es de otra familia. Pero TREND_4H tope 7 d, también con universo dinámico top 20 (`results/evaluaciones/2026-11-04-trend4h-t7-universo-dinamico.json`), ya miró el holdout de 2025-09 en adelante con el mismo intervalo, el mismo universo y rupturas de 20 velas. La spec misma admite que una ruptura de la caja suele ser también una ruptura de Donchian 20. Como pusiste `familia: ruptura` y TREND_4H no está en ella, la evaluación no lo va a deducir sola: el comentario «manda ella» no protege. Recomiendo `holdout_contaminado: true`, o leer el holdout como poco informativo.
- Familia: `pruebas_previas: 14` cuenta lo de btc-signal-web pero no las 3 variantes TREND_4H de este repo (tope 7 d, control 14, universo dinámico). Es conservador igual, pero conviene anotarlo.
- Costos: la hipótesis dice que el stop está «a varios ATR». Pero una caja comprimida es estrecha por definición, y el ATR14 también se achica en la compresión. Muchas entradas pueden quedar en el piso de 1 ATR. Con 0.1%/lado y un ATR de 4h de ~0.6% (BTC en calma), la comisión pesa ~0.3R, no 0.05–0.1R. Además el stop se calcula desde el cierre de t y la entrada es en la apertura de t+1, así que la distancia real puede ser algo menor.
- Alcance: el tope de 42 velas (7 d) más el trailing de 2 ATR garantizan una mediana ≤ 7 días. Está bien.
- Universo: `dinamico: {top: 20}`, sin sesgo de supervivencia. Está bien. La madre TREND_4H es un control adecuado para ver si la compresión agrega algo.

Archivos revisados:
/home/user/backtesting-strategies/specs/2026-11-11-compresion-ruptura-4h.yaml
/home/user/backtesting-strategies/src/bt/strategies/compresion_ruptura.py
/home/user/backtesting-strategies/tests/test_estrategia_compresion_ruptura.py
