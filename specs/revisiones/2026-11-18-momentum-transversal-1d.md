veredicto: observaciones
2026-11-18-momentum-transversal-1d

- Repetida: no. El único antecedente es el momentum relativo semanal de btc-signal-web (`decisiones.md`, rechazado el 2026-10-11). La spec lo declara en `ya_probado`. El mecanismo es distinto: regla diaria, stop y trailing en ATR, universo dinámico, resultado en R. No bloquea.
- Snooping: lookback=7 y k=3 salen de la literatura (Liu, Tsyvinski & Wu), y se declara el cambio respecto de la idea #17 ("1–3 días"). Hay UNA configuración y el sentido está fijado. Ojo: el 7 también coincide con el horizonte del momentum semanal que ya miró el holdout. Está declarado en `holdout_contaminado: true`, así que como máximo da observación.
- Criterio: es al menos tan exigente como `PLANTILLA.yaml`. Tiene `ic95_excluye_cero`, `ajuste_por_pruebas`, `supera_nulo_p95`, `tramos_positivos_minimo` 3, `estabilidad_minima` 0.5 y el holdout completo. `n_minimo` 300 supera los 100 de la plantilla.
- Familia: `corte_transversal` es nueva y `pruebas_previas: 1` coincide con la prueba de btc-signal-web. No hay otras variantes en este repo. No hace falta `madre`.
- Universo: `dinamico` top 20 sin sesgo de supervivencia. La pertenencia al universo usa el volumen del mes anterior, no mira el futuro.
- Costos: con 0.1% por lado y stop de 2 ATR diario (5–7%), la comisión pesa unas 0.03–0.04R. Razonable; `funding: true` suma el costo de la pata corta.
- Alcance: tope de 5 velas diarias, así que la mediana queda en 5 días o menos.
- Look-ahead en el código: no encontré. El retorno usa `shift(+lookback)`, el ATR sólo mira hacia atrás y no hay `rolling` centrado.
- Test: 6 passed. Llama a `chequear_lookahead_corte` con los params de la spec. Límite: el chequeo no pasa `miembros`, así que la rama de membresía mensual no queda cubierta por ese chequeo (no es riesgo real).
- Riesgo estadístico (ya declarado en la spec): las señales diarias de 3+3 símbolos del mismo mercado no son independientes, y el IC de ±2 EE es optimista. El control nulo y los tramos son el contrapeso. La dirección neta no está neutralizada por beta.
