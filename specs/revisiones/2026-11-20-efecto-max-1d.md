veredicto: ok
2026-11-20-efecto-max-1d

- Repetida: no. `decisiones.md` cerró el momentum de corte transversal (7d y 1d, 2026-11-19) y dejó abierto el efecto MAX como mecanismo distinto, y la spec lo explica. No hay otra spec de efecto MAX.
- Fiel a la idea 20: sí. Mismo ranking (MAX de 30 días), largo el extremo alto y corto el bajo, top 20 dinámico, tenencia ≤ 7 d, stop en ATR y signo de continuación. Sin desvíos.
- Snooping: una sola configuración (30, k=3, stop y trailing 2 ATR, tope 7 d) tomada de la idea y de las specs hermanas. No hay números de corridas previas.
- Criterio: igual o más exigente que PLANTILLA (`n_minimo` 300, `ic95_excluye_cero`, `ajuste_por_pruebas`, `supera_nulo_p95`, `tramos_positivos_minimo` 3, `estabilidad_minima` 0.5, holdout endurecido). Es cribado con `solo_desarrollo: true` y no toca el holdout.
- Familia: `corte_transversal`, `pruebas_previas: 1` y `holdout_contaminado: true`, declarados. Sin `madre`: no es variante de una estrategia con madre. Conviene confirmar que `n_pruebas` salga 3.
- Universo: `dinamico: {top: 20}`, futuros, con funding. Sin sesgo de supervivencia.
- Costos: 0.1% por lado más funding; ~0.03–0.04R por operación con stop de 2 ATR diario.
- Alcance: trailing de 2 ATR y tope de 7 d; mediana ≤ 7 d plausible.
- Look-ahead: sin hallazgos. Hueco menor: el test llama a `chequear_lookahead_corte` sin `miembros`, así que la rama del universo dinámico (un `isin` por mes de `t`, sin futuro) no queda cubierta.
- Riesgo residual, ya declarado: la dirección neta no está neutralizada por beta y las muestras se solapan (el IC de ±2 EE es optimista; el control nulo y los tramos hacen de contrapeso).
