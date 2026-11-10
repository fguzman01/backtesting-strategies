veredicto: observaciones
2026-11-10-continuacion-volumen-4h

- Código sin look-ahead. `continuacion_volumen.py` usa `volume.shift(1).rolling(180).quantile`, así que la vela actual no entra en su propia referencia. El retorno es `close[t] - close[t-6]`, sin `shift(-k)` ni rolling centrado. El test llama a `chequear_lookahead` con los params de la spec. Los 4 tests pasan y `bt.spec` valida la spec.
- Criterio: igual de exigente que `PLANTILLA.yaml` en todas las claves (`ic95_excluye_cero`, `ajuste_por_pruebas`, `supera_nulo_p95`, `tramos_positivos_minimo: 3`, `estabilidad_minima: 0.5` y holdout estricto). `n_minimo: 300` es más duro que los 100 de la plantilla. Universo `dinamico: {top: 20}`. Un solo set de parámetros fijado y sin números salidos de una corrida previa.
- Idea no cerrada: `decisiones.md` no tiene volumen × retorno como disparador. La rechazada `2026-11-03-reversion-salto-liquidaciones-1h` comparte el disparador de shock de volumen, pero va en dirección opuesta, con 1h y retorno de 24 h en vez de un salto. `ya_probado` lo reconoce. Que aquel resultado fuera −0.185 aporta poca evidencia a favor de ésta. Queda como riesgo de familia, no de repetición.
- Evidencia débil: la fuente es un paper leído sólo por el resumen (evidencia C). La spec ya admite que el efecto de 12–24 h puede ser menor que una vela de 4h. El stop de 2 ATR, el trailing de 2 ATR y el umbral de 2 ATR son elecciones razonables pero no derivadas del paper.
- `holdout_contaminado: false` es defendible porque la regla es nueva. Pero la madre TREND_4H ya miró el holdout 3 veces (`decisiones.md`), y el cupo y los tokens son los mismos. La spec lo declara y dice que manda la evaluación. Conviene que el reporte lo cite.
- `pruebas_previas: 0` con familia nueva está bien. `madre` está declarada, con `timeout_velas: 42` (7 días) como control.
- Costos: la comisión de 0.1% por lado contra un stop de ~2 ATR en 4h (varios %) da una comisión en R baja, del orden de 0.05R. El supuesto de deslizamiento incluido es razonable. Entrar justo tras un pico de volumen puede ser peor que 0.05%, pero `aguanta_costos` ×1.5 en el holdout lo cubre.
- Alcance: `timeout_velas: 18` son 3 días, así que la mediana queda ≤ 7 días.
- Solapamiento: un movimiento de 2 ATR con volumen suele coincidir con una ruptura de Donchian. La señal puede ser TREND_4H disfrazada, y el cupo de 3 por dirección puede correlacionarlas. Sería útil que el reporte mida cuántas entradas coinciden con la madre.
- Menor: `atr_n` es 14 aquí y 20 en la madre. No sesga, pero hace la comparación menos limpia.
