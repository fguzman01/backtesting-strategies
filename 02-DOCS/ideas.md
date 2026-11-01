# Cola de ideas

De acá toma la rutina diaria la próxima estrategia a pre-registrar (Fase 4). Las ideas las
agregan Felipe, la rutina al investigar, o el auditor al revisar rechazadas.

Una idea **no es una spec**: no tiene criterio todavía. Antes de convertirla, la rutina revisa
`decisiones.md` (que no esté medida) y `alcance.md` (que entre en el horizonte).

**Estados:** `propuesta` (falta el visto bueno de Felipe) · `en cola` (lista para pre-registrar) ·
`pre-registrada` (ya tiene spec) · `descartada` (con el motivo).

**Ideas que nacen de una rechazada:** tienen que nombrar a la madre, explicar el mecanismo nuevo
(no un parámetro afinado) y contar cuántas variantes de esa familia se evaluaron. La rechazada no
se re-evalúa nunca; esto es una pregunta nueva con su propio pre-registro.

| # | Idea | Origen | Mecanismo / por qué podría funcionar | Riesgo de snooping | Estado |
|---|---|---|---|---|---|
| 1 | TREND_1D con salida por trailing en ATR que deje correr las tendencias, pero con tope de 14 días en vez de 7 | Auditoría de `2026-10-31-trend1d-tope-7d` (rechazada al borde: IC [−0.001, +0.175]) | El diagnóstico mostró que el edge está en pocas tendencias largas: un tope fijo de 7 días las corta. El alcance permite hasta 14 días de tope si la mediana queda ≤ 7. | Familia TREND_1D: 1 variante evaluada en este repo. Alto si se prueban varios topes: elegir UNO antes de correr | pre-registrada (2026-11-01-trend1d-chandelier-14d): chandelier 22 velas − 3 ATR, tope 14d |
| 2 | Tendencia en 4h dentro del alcance (TREND_4H de btc-signal-web con tope de 7 días) | `decisiones.md`: TREND_4H pasó desarrollo (+0.231, n=3568) y holdout más débil | Más operaciones y más cortas que la diaria; la comisión en 4h todavía es baja en R (stops de varios ATR) | Holdout ya mirado en btc-signal-web: este repo debería usar sólo desarrollo hasta tener un holdout nuevo | en cola (Felipe, 2026-11-01) |
| 3 | TREND_1D con trailing en ATR **real** (máximo desde la entrada − k·ATR, tope 14 d), una vez que el motor le pase la posición abierta a la estrategia | Auditoría 2026-11-01 de `2026-11-01-trend1d-chandelier-14d` (rechazada; la salida chandelier sin estado casi nunca actuó: mediana = tope, 14.0 d) | La hipótesis «trailing que deje correr tendencias» nunca se midió: el trailing sin estado no disparó. Un trailing que sube con el máximo desde la entrada cortaría las perdedoras antes y debería bajar la mediana hacia el alcance (≤ 7 d). Requiere cambio de motor (mejora 4 de la auditoría) | Familia TREND_1D: 2 variantes evaluadas, esta sería la 3.ª. Alto: elegir UNA k antes de correr. Si la mediana sigue > 7 d es un tema de alcance, no de parámetros | propuesta |
