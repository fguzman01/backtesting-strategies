veredicto: observaciones
2026-11-05-overnight-nyse-max10-1h

- Repetida, con mecanismo parcial. `decisiones.md` cierra con "No" la estacionalidad por hora y por bloque de 4h (2026-10-20). Esta spec agrega un filtro de estado (máximo de 10 días) y una ventana de 18h. Lo declara en `ya_probado` y no copia parámetros. El mecanismo es distinto, pero el riesgo de fondo es el mismo: el mejor bloque previo fue +0.114% bruto, contra 0.2% de costo ida y vuelta.
- Parámetros: se fijó UNA configuración (10, ATR 24, stop 6, 16 ET, 10 ET). El 10 viene de la fuente (Quantpedia/Gemini), no de una corrida local. Las horas 16/10 ET copian la regla de la fuente. No vi snooping propio, pero la fuente tiene un corte fuera de muestra elegido a dedo, como admite la hipótesis.
- Criterio: iguala o supera `PLANTILLA.yaml` (IC95, ajuste por pruebas, nulo p95, tramos ≥3, holdout estricto). `n_minimo` es 150, más exigente que los 100 de la plantilla. No afloja nada.
- Familia: `estacionalidad`, `pruebas_previas: 3` (hora, bloque de 4h y día de la semana, todas en btc-signal-web). Cuenta como la 4.ª variante. `holdout_contaminado: true` declarado y justificado. Sin `madre`: no hace falta.
- Universo: sólo BTCUSDT con historia spot, justificado en la hipótesis (la evidencia de origen es de BTC). Sesgo de supervivencia bajo.
- Costos: 0.1% por lado sobre un stop de ~3% da unas 0.07R. Un overnight de BTC con edge bruto menor a ~0.2% por operación pierde. Es el punto más probable de fallo.
- Alcance: salida por regla a las 18h y `timeout_velas` 24, la mediana queda muy por debajo de 7 días. Cumple.
- Look-ahead en el código: no encontrado. El máximo de 240 cierres incluye sólo la vela de la señal y el pasado; el ATR es de la vela de la señal; entra en la apertura de t+1; `salida_largo` marca la vela de las 09 ET y el motor cierra en la apertura de las 10 ET. El cambio de hora está probado en el test.
- Test: `chequear_lookahead` con los params de la spec y una variante; pasan los 5 tests.
- Evidencia débil (C) y holdout contaminado: como mucho llega a OBSERVACION, como dice la propia spec.
