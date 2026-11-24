veredicto: observaciones
2026-11-24-volatilidad-realizada-1d

- Código sin look-ahead. VOL usa cierres hasta `t` (rolling(30) con ventana completa), el ATR es causal y la entrada en `t+1` la hace el motor. El test llama a `chequear_lookahead_corte` con los params de la spec. `pytest` da 6 passed y `bt.spec` valida sin errores.
- Fiel a la idea #23: ventana 30, k=3, top 20 dinámico, largo baja vol y corto alta vol, tope 7 d, stop en ATR. Es UNA configuración, tomada de la idea y no de datos. El sentido inverso queda descartado de forma explícita.
- Criterio igual de exigente que la plantilla: `ic95_excluye_cero`, `ajuste_por_pruebas`, `supera_nulo_p95`, `tramos_positivos_minimo: 3`, `estabilidad_minima` y el holdout completo. Sube `n_minimo` a 300. Es cribado (`solo_desarrollo`) y declara `holdout_contaminado: true`.
- Pregunta emparentada con cerradas. La familia `corte_transversal` ya tiene 4 specs en este repo (momentum x2, MAX, beta) más 1 externa. Las anteriores dieron cero y la auditoría del 2026-11-22 pidió no abrir variantes sin mecanismo realmente nuevo. El mecanismo (dispersión de retornos) se distingue, pero comparte la tesis «lotería» con MAX y beta. El listón de Bonferroni será alto, y la spec lo reconoce.
- Sesgo de composición: el corto de alta vol es de beta alta y el largo de baja vol de beta baja; en mercado alcista la cartera queda neta corta de mercado. Un resultado puede ser beta y no premio por varianza. La idea pedía el nulo «en el mismo mes» y control de régimen; la spec sólo menciona «control nulo y tramos». Conviene explicitarlo al leer el resultado.
- Costos: 0.1% por lado y stop de 2 ATR. Para largos de baja vol (ATR ~0.5–1%) la comisión en R ronda 0.1–0.2R: al borde. Los de baja vol pueden tener stops estrechos que saltan por ruido.
- Muestras solapadas: el IC de ±2 EE es optimista; la spec lo declara.
- Alcance: mediana esperada 3–4 días, tope 7, dentro del límite.
