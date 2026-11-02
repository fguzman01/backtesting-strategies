# Cola de ideas

De acá toma la rutina diaria la próxima estrategia a pre-registrar (Fase 4). Las ideas las
agregan Felipe, el **explorador** cada semana (desde su catálogo `02-DOCS/catalogo.md`), el
investigador cuando la cola se vacía, o el auditor al revisar rechazadas.

Una idea **no es una spec**: no tiene criterio todavía. Antes de convertirla, la rutina revisa
`decisiones.md` (que no esté medida) y `alcance.md` (que entre en el horizonte).

**Estados:** `propuesta` (falta el visto bueno de Felipe) · `en cola` (lista para pre-registrar) ·
`pre-registrada` (ya tiene spec) · `descartada` (con el motivo).

**Entrada automática a la cola** (Felipe, 2026-11-02): el explorador pasa solas a `en cola` las ideas
con evidencia A o B, dentro del alcance, de familias no cerradas, no medidas antes e implementables
con el motor actual; como mucho 2 por familia y 5 por semana. El resto entra como `propuesta`.
Felipe puede descartar o reordenar cualquiera.

**Ideas que nacen de una rechazada:** tienen que nombrar a la madre, explicar el mecanismo nuevo
(no un parámetro afinado) y contar cuántas variantes de esa familia se evaluaron. La rechazada no
se re-evalúa nunca; esto es una pregunta nueva con su propio pre-registro.

| # | Idea | Origen | Mecanismo / por qué podría funcionar | Riesgo de snooping | Estado |
|---|---|---|---|---|---|
| 1 | TREND_1D con salida por trailing en ATR que deje correr las tendencias, pero con tope de 14 días en vez de 7 | Auditoría de `2026-10-31-trend1d-tope-7d` (rechazada al borde: IC [−0.001, +0.175]) | El diagnóstico mostró que el edge está en pocas tendencias largas: un tope fijo de 7 días las corta. El alcance permite hasta 14 días de tope si la mediana queda ≤ 7. | Familia TREND_1D: 1 variante evaluada en este repo. Alto si se prueban varios topes: elegir UNO antes de correr | pre-registrada (2026-11-01-trend1d-chandelier-14d): chandelier 22 velas − 3 ATR, tope 14d |
| 2 | Tendencia en 4h dentro del alcance (TREND_4H de btc-signal-web con tope de 7 días) | `decisiones.md`: TREND_4H pasó desarrollo (+0.231, n=3568) y holdout más débil | Más operaciones y más cortas que la diaria; la comisión en 4h todavía es baja en R (stops de varios ATR) | Holdout ya mirado en btc-signal-web: este repo debería usar sólo desarrollo hasta tener un holdout nuevo | en cola (Felipe, 2026-11-01) |
| 3 | TREND_1D con trailing en ATR **real** (máximo desde la entrada − k·ATR, tope 14 d), una vez que el motor le pase la posición abierta a la estrategia | Auditoría 2026-11-01 de `2026-11-01-trend1d-chandelier-14d` (rechazada; la salida chandelier sin estado casi nunca actuó: mediana = tope, 14.0 d) | La hipótesis «trailing que deje correr tendencias» nunca se midió: el trailing sin estado no disparó. Un trailing que sube con el máximo desde la entrada cortaría las perdedoras antes y debería bajar la mediana hacia el alcance (≤ 7 d). Requiere cambio de motor (mejora 4 de la auditoría) | Familia TREND_1D: 2 variantes evaluadas, esta sería la 3.ª. Alto: elegir UNA k antes de correr. Si la mediana sigue > 7 d es un tema de alcance, no de parámetros | propuesta |
| 4 | Momentum intradía: dirección de la primera media hora (00:00–00:30 UTC o apertura de sesión) para operar la última | catálogo: Momentum intradía de series de tiempo | Provisión de liquidez al cierre empuja a favor de la primera media hora (Shen et al. 2022) | Medio: elegir UNA ventana antes de correr. Comisión 0.1% contra un movimiento de 30 min es el riesgo central | propuesta (explorador, 2026-11-02; no pude leer el paper para confirmar costos) — ojo: btc-signal-web midió que ninguna hora ni bloque de 4h paga la comisión (`decisiones.md`); sólo vale si el mecanismo condicional es distinto |
| 5 | Largo fijo en la ventana ~21:00–23:00 UTC en BTC 1h | catálogo: Estacionalidad por hora UTC | Retornos concentrados en la noche UTC según Padyšák y Vojtko; un estudio de 2017 no halla patrón | Alto: ventana elegida mirando datos; fijar 21→23 antes de correr y exigir tramos | descartada: ya medida en btc-signal-web (estacionalidad, 2026-10-20: ninguna hora paga la comisión). Ver `decisiones.md` |
| 6 | Regla condicional día/noche (reversión diurna, deriva nocturna) en BTC y ETH 1h | catálogo: Reversión/momentum por sesión | Sobrerreacción de día, deriva de noche (MDPI JRFM 2026) | Alto: el propio paper muestra que la regla de 2016–2020 se degrada en 2021–2025 | propuesta (explorador, 2026-11-02; evidencia C) — ojo: btc-signal-web midió que ninguna hora ni bloque de 4h paga la comisión (`decisiones.md`); sólo vale si el mecanismo condicional es distinto |
| 7 | Contrarian por funding extremo (percentil alto → corto; bajo → largo) en perps 1h–4h, con stop amplio | catálogo: Funding extremo como señal direccional | Largos saturados son liquidables; el funding ya está en el motor | Medio: elegir percentil y ventana antes de correr. Extrapolación mía, sin paper directo (evidencia D) | descartada: ya medida en btc-signal-web (funding contrarian, 2026-10-20: el funding alto anuncia continuación, no giro). Ver `decisiones.md` |
