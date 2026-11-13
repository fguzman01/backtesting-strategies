veredicto: observaciones
2026-11-13-trend4h-t7-vs-madre

- Repetida: no. `decisiones.md` mide T7 y sus controles de universo, pero ninguna compara T7 con su madre en 4h.
- Snooping: ok. Una sola comparación, la regla 20/10/20/200/2.0 es la original; el tope de 84 velas es el máximo del alcance, no un valor optimizado.
- Criterio: sin `ajuste_por_pruebas` ni `estabilidad_minima`; aceptable porque es `medicion: true` + `solo_desarrollo: true` y nunca llega a `approved.json`. La regla de interpretación (hija − madre ±2 EE) está fijada de antemano en la hipótesis.
- Riesgo principal: hija y madre comparten las señales de entrada y difieren sólo en la salida por timeout, así que las muestras están muy emparejadas. Si el EE de la diferencia se calcula como si fueran independientes, queda sobreestimado y el intervalo casi siempre incluirá 0: «el tope no cambia nada medible» sería falta de potencia, no equivalencia. Al leer el resultado, no tomarlo como equivalencia; conviene reportar cuántos trades difieren.
- Familia y contaminación: `holdout_contaminado: true`, `solo_desarrollo: true` y `madre` declarados; `pruebas_previas: 4` coherente.
- Universo y costos: igual que la original; el sesgo de supervivencia afecta igual a hija y madre.
- Alcance: mediana esperada 3 d (≤ 7 d); madre con 84 velas = 14 d, dentro del máximo.
- Look-ahead: sin código ni test nuevos; `tendencia_donchian` es la misma estrategia de la original.

Archivo revisado: specs/2026-11-13-trend4h-t7-vs-madre.yaml
