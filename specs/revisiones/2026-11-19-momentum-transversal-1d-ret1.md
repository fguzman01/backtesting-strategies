veredicto: observaciones
2026-11-19-momentum-transversal-1d-ret1

(Segunda revisión; la primera dio «bloquea» por dos puntos, corregidos sin mirar datos: el test de look-ahead con `lookback=1` en `tests/test_estrategia_momentum_transversal_ret1.py` y la declaración de `madre`.)

- Repetida: no es una pregunta cerrada. Es la mitad sin medir de la idea #17. Lo único que cambia respecto de la madre rechazada (`2026-11-18-momentum-transversal-1d`, lookback 7, −0.012) es el horizonte (1 día en vez de 7). El mecanismo declarado (flujos escalonados en las más líquidas) es una justificación débil: en la práctica es otro valor de un parámetro de la misma familia. La spec lo admite y fija una sola configuración; la reversión no se prueba aparte.
- Snooping: ok. `lookback=1`, `k=3` y stop/trailing de 2 ATR son los mismos de la madre. No hay números tomados de corridas ni del holdout.
- Criterio: igual de exigente que `PLANTILLA.yaml` (`ic95_excluye_cero`, `ajuste_por_pruebas`, `supera_nulo_p95`, `tramos_positivos_minimo: 3`, holdout estricto). `n_minimo` 300. No afloja nada.
- Familia: `corte_transversal`, `madre` declarada, `pruebas_previas: 1` (btc-signal-web) y `holdout_contaminado: true`. Esta sería la 3.ª prueba, así que el margen del IC sube solo. Con la contaminación, lo máximo alcanzable es observación (solo paper).
- Universo: `dinamico top 20`, sin sesgo de supervivencia. Ok.
- Costos: 0.1% por lado y stop de 2 ATR diario (~5–7%): ~0.03–0.04R de comisión. El riesgo real es que un retorno de 1 día rebota y se rota cada día; la spec ya lo declara.
- Alcance: tope de 5 velas diarias, mediana ≤ 7 días. Ok.
- Look-ahead: no encontré. `senales_corte` usa sólo `shift(lookback)` hacia atrás, el `rank` es por fila y el ATR sale de datos hasta `t`. El test llama a `chequear_lookahead_corte` con los params de la spec.
- Hueco menor del test: no pasa `miembros`, así que el filtro por mes de vigencia no queda cubierto por el chequeo anti look-ahead. Riesgo bajo (la pertenencia se define por mes calendario).
- Evidencia de la fuente: C+, sólo resúmenes. Prior bajo: la madre de 7 días no pagó y la reversión de 1 día domina en el resto del universo. Si esta también cae, la familia queda cerrada.
