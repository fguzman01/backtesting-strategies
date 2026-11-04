# Preguntas ya cerradas

**Antes de proponer evaluar una estrategia, parámetro o activo, buscá acá.** Indexado por la
pregunta. Una línea por pregunta; el detalle va en el commit o en el reporte.

Origen: resumen de `fguzman01/btc-signal-web/DECISIONES.md` al 2026-10-31, completado el 2026-11-02
(la primera migración había dejado afuera funding, estacionalidad, pares, miedo extremo y otras). Ese archivo sigue
siendo la fuente con todos los números; si hay duda, leer la fila original.

> ⚠️ Los avgR de btc-signal-web medidos **antes del 2026-10-11** son optimistas (compuerta y
> llenado usaban el mismo parámetro). Re-medir antes de citar.

## Estrategias (medidas en btc-signal-web)

| Pregunta | Veredicto | Cuándo |
|---|---|---|
| ¿Momentum relativo cross-sectional (largo top-3 / corto bottom-3, rebalanceo semanal)? | **No.** Desarrollo +1.0%/semana, holdout −0.56% y 1/4 tramos. Rechazado contra criterio pre-registrado | 2026-10-11 |
| ¿Motor de tendencia en 1h (escala 15m→30m→1h)? | **Sí.** Mejora monótona con la temporalidad; 1h desarrollo +0.188 (n=1323), holdout +0.157 (n=417), 4/5 positivos | 2026-10-11 |
| ¿Reversión a la media / rangos / comprar piso de canal, con stop? | **No.** 5 diseños × 2 temporalidades, todos negativos antes de comisiones. El precio vuelve, pero tras excursiones que un stop de 1.5 ATR corta | 2026-08-31 |
| ¿Oro (XAU/PAXG) con estrategias intradía? | **No.** Edge bruto +0.08R contra comisión 0.15R | 2026-09-28 |
| ¿Oro en diario (SWING_1D)? | **Sí, en producción.** Re-medido con modelo corregido: desarrollo +0.102 n=35, tramos −−++, el intervalo toca el cero | 2026-09-29 / 10-11 |
| ¿TREND_1D (Donchian 20/10 sin techo) en oro? | **No.** Desarrollo +0.022 ±0.51 n=37; entradas al azar rinden más. Holdout no mirado | 2026-10-24 |
| ¿Motor diario sobre velas de 4h (punto medio)? | **No.** 0 de 16 tramos positivos; edge bruto ya negativo | 2026-09-29 |
| ¿Sesiones en oro (ruptura rango asiático en apertura de Londres)? | **No.** Ninguna ventana distinguible de cero | 2026-09-29 |
| ¿SCALP_5M_PULLBACK (5m o 15m)? | **No, retirada.** Holdout BTC 5m −0.233 ±0.056 | 2026-09-30 |
| ¿SCALP_5M_BREAKOUT (5m o 15m)? | **No, retirada.** 12 configuraciones, ninguna con intervalo fuera del cero | 2026-09-30 |
| ¿SCALP_15M en qué símbolos? | 8 de 14 pasan (UNI, ADA, DOGE, NEAR, AVAX, XRP, LINK, ETH). No: BTC, SOL, BNB, TRX, DOT, LTC | 2026-09-30 |
| ¿Por qué SCALP_15M rinde peor en vivo que en backtest? | **Abierta.** Vivo −0.389 ±0.313 (n=30) vs backtest +0.151. Deslizamiento explica sólo parte | 2026-10-11 |
| ¿Exigir más tendencia (ADX 4h ≥ 25) en SCALP_1H? | **No.** Ni el puntaje más alto muestra edge | 2026-10-18 |
| ¿Ir CONTRA el funding extremo (corto tras funding muy alto, largo tras muy bajo)? | **No, al revés.** Corto tras funding en su percentil ≥95 de 90 días: −4.78% a 7 días (n=1587, pierde en los 14 tokens). El funding alto anuncia continuación, no giro. Exploración, sólo desarrollo | 2026-10-20 |
| ¿Comprar después de un funding extremadamente alto gana más que comprar cualquier día? (FUNDING_ALTO) | **No.** Rechazado contra criterio pre-registrado: +4.02% a 7 días, pero comprar al azar en el MISMO mes rinde más (p50 +6.80%): lo que se veía era el mes alcista, no el funding. Holdout no mirado | 2026-10-20 |
| ¿Carry de funding (largo spot + corto perp)? | Real pero chico y achicándose; además es una posición cubierta de dos activos y de semanas (fuera del alcance y del motor) | 2026-10-20 |
| ¿Hay estacionalidad aprovechable (hora del día, bloque de 4 h, día de la semana)? | **No.** Ninguna hora (1h, desde 2023-09) ni bloque de 4h paga la comisión de 0.2% ida y vuelta (mejor bloque 04-08 UTC: +0.114% bruto → −0.086% neto). Los mejores días (miércoles, sábado) quedan dentro del ruido frente al día promedio alcista | 2026-10-20 |
| ¿Sirve operar pares (stat-arb: spread entre dos tokens que vuelve a la media)? | **No.** Exploración, sólo desarrollo: nada que pre-registrar | 2026-10-20 |
| ¿Comprar BTC en diario con miedo extremo (índice < 25), solo o con funding bajo? | **No.** Rechazado contra criterio pre-registrado: sólo miedo es peor que el azar; con funding bajo no pasa el nulo y el holdout da −3.23% | 2026-10-18 |
| ¿SWING_1D (ruptura diaria a favor del régimen semanal) en las altcoins? | **No.** Rechazado: desarrollo n=138, −0.034 [−0.185, +0.117], depende del régimen y casi no opera (~25 por año en 14 tokens) | 2026-10-20 |
| ¿El backtest por cierres de vela sirve para aprobar un scalp? ¿SCALP_1H / SCALP_30M tienen edge? | **No sirve, y con el modelo fiel no tienen edge.** Por cierres sabe una vela antes qué rupturas se sostienen. Con el modelo fiel (vela en formación, puertas, tope de deslizamiento 0.6R): SCALP_1H 14 tokens +0.160 → **−0.099** (0/14 positivos); SCALP_30M SOL +0.157 → −0.123. **Un scalp de ruptura sólo se puede evaluar con un motor intra-vela** | 2026-10-13 |
| ¿Las perdedoras de SCALP_1H comparten un patrón visible al abrir? ¿Tendencia vs lateral? | **No:** ninguna de 12 variables las separa, y tampoco tendencia vs lateral | 2026-10-28 |
| ¿Cómo limitar la tendencia diaria? ¿Limitar posiciones corta las ganadoras? | **Máx. 5 por dirección**, y limitar mejora el resultado ajustado por riesgo (los primeros en romper capturan el movimiento; los siguientes son la misma apuesta) | 2026-10-20 |

## Parámetros (medidos en btc-signal-web)

| Pregunta | Veredicto | Cuándo |
|---|---|---|
| ¿Cerrar 100% en TP1 o parcial + breakeven + TP2? | **100% en TP1.** El parcial pierde en 12 de 14 series | 2026-09-17 / 10-01 |
| ¿TP1 más ambicioso que 1R? | **1.5R en 15m/30m**, validado fuera de muestra (21 de 22 series). No en 5m | 2026-10-02 |
| ¿Abrir el techo (TP2 > 2R o trailing)? | **No.** Plano entre 2R y 3R, empeora más allá | 2026-10-11 |
| ¿Timeout? | 480 min en 5m/15m/30m. "Sin límite" bloquea posiciones y desploma n | 2026-10-01 |
| ¿Cooldowns tras SL cambian el backtest? | **No.** −0.0001R de delta medio | 2026-10-11 |
| ¿Guarda de R:R mínimo? | **No.** Empeora la muestra | 2026-09-22 |
| ¿Relajar o acelerar la compuerta de tendencia 4h (EMA200→EMA100/50)? | **No** en ambos sentidos | 2026-09-17 / 10-08 |
| ¿Cerrar 50% o 75% en TP1 y dejar el resto a TP2 con stop a la entrada, en SCALP_1H? | **No:** las cuatro variantes quedan levemente peor que cerrar 100% en TP1 (TP2 queda muy cerca de TP1) | 2026-10-17 |
| ¿Mover el stop a la entrada ANTES de TP1, cuando ya va ganando? | **No: empeora o no cambia.** Salir en cero cuesta la comisión (~0.1R) y muchas operaciones vuelven a la entrada antes de seguir al TP | 2026-10-17 |
| ¿Acercar el TP1 porque muchas quedan cerca sin tocarlo? | **No:** pasa en 6-8% de las operaciones, pero acercar el TP1 empeora; alejarlo mejora apenas. El problema grande son las entradas | 2026-10-17 |

## Aprendizajes estructurales

- La frontera que decide es **comisión / stop**, no la temporalidad: stops más anchos (marcos
  mayores) pagan mucho menos comisión en R.
- Las estrategias de btc-signal-web son **seguimiento de tendencia calibrado en cripto**; no
  transfieren a oro intradía.
- Varias estrategias dependen del **régimen** más de lo que rinden: siempre mirar tramos.

## Medidas en este repo

| Pregunta | Veredicto | Cuándo | Reporte |
|---|---|---|---|
| ¿El motor de este repo reproduce los resultados de btc-signal-web? | **Sí, para TREND_1D.** 14 tokens desarrollo n=568 +0.541 (registrado n=567 +0.545); holdout n=107 +0.258 (107, +0.256); oro desarrollo n=37 +0.029 (37, +0.022). Paridad exacta operación por operación con el script original en datos sintéticos. Pendiente: estrategias de scalp/swing intradía (motor TS) | 2026-10-31 | `validacion.yml`, run 41233661837 |
| ¿TREND_1D sigue teniendo edge si se corta a los 7 días (para entrar en el alcance)? (`2026-10-31-trend1d-tope-7d`) | **RECHAZADA, por muy poco.** Desarrollo 2020-07→2025-09, 14 tokens, n=952, **+0.087 [−0.001, +0.175]**: el intervalo toca el cero por una milésima. Sí le gana al azar (nulo p95 +0.080) y 3/4 tramos positivos. Sin tope era +0.545: el tope se come la mayor parte del edge, que vive en pocas tendencias largas. Holdout NO mirado | 2026-10-31 | `results/reports/2026-10-31-trend1d-tope-7d.md` |
| ¿TREND_1D con salida por trailing en ATR (chandelier) y tope de 14 días conserva el edge dentro del alcance? (`2026-11-01-trend1d-chandelier-14d`) | **RECHAZADA.** desarrollo n=814 +0.148 [+0.022, +0.274]. No pasa: «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-07-23:+0.51R 2022-01-06:-0.15R 2023-05-09:+0.14R 2024-07-16:+0.09R): depende del régimen; la dispersión entre tramos (0.67R) supera el doble del avgR (0.148R)); «alcance: duración mediana ≤ 7 días» (14.0 días) | 2026-11-01 | `results/reports/2026-11-01-trend1d-chandelier-14d.md` |
| ¿Se hace una excepción de alcance para la tendencia diaria, que gana más con operaciones de semanas? | **No (Felipe, 2026-11-01).** Se espera TREND_4H con tope de 7 días; si falla, se cierra la familia de tendencia en la factory. Ver `02-DOCS/alcance.md` | 2026-11-01 | `02-DOCS/auditorias/2026-11-01.md` |
| ¿La tendencia en 4h (Donchian 20/10, stop 2 ATR, filtro EMA200) con tope de 7 días tiene edge neto dentro del alcance? (`2026-11-02-trend4h-tope-7d`) | **APROBADA.** desarrollo n=4631 +0.245 [+0.178, +0.312]. holdout n=916 +0.036 | 2026-11-02 | `results/reports/2026-11-02-trend4h-tope-7d.md` |
| ¿Medir en los 14 tokens que siguen vivos sesga los resultados? | **Sí, por construcción (sesgo de supervivencia).** Desde 2026-11-03 las specs nuevas usan por defecto `universo.dinamico` (los más operados de cada mes, con los retirados). Las evaluaciones anteriores quedan como están; cuánto cambia el número en una estrategia ya aprobada es una pregunta nueva, con su spec | 2026-11-03 | `02-DOCS/reglas-de-medicion.md` |
| ¿Hay que exigir más cuando una familia ya probó muchas variantes? | **Sí (Felipe, 2026-11-04, B-02).** `ajuste_por_pruebas`: el margen sobre el cero sube con `n_pruebas` (Bonferroni: 8 variantes → 2.73 EE). Por defecto en las specs nuevas | 2026-11-04 | `02-DOCS/reglas-de-medicion.md` |
| ¿Cómo se detecta una estrategia que sólo funciona con sus números exactos? | **Estabilidad de parámetros**: al pasar desarrollo se corre con todos los parámetros ×0.8 y ×1.2. Informa por ahora; `estabilidad_minima` en la spec lo vuelve criterio | 2026-11-03 | `02-DOCS/reglas-de-medicion.md` |
| ¿Cómo se renueva la evidencia cuando el holdout ya se miró? | **Prueba hacia adelante mensual** (`bt.adelante`, `adelante.yml`): cada aprobada u observación sobre los datos posteriores a su evaluación. Sugiere subir o bajar de nivel; decide Felipe | 2026-11-03 | `results/reports/adelante.md` |
| ¿Una aprobada con holdout débil o ya mirado va al bot igual que una sólida? | **No (btc-signal-web, 2026-11-02).** Dos niveles: `aprobada` (holdout estricto y limpio) y `observacion` (sólo paper). `2026-11-02-trend4h-tope-7d` se **reclasifica a observación**: holdout débil y contaminado (btc-signal-web ya había mirado ese período con TREND_4H). El veredicto registrado no cambia; cambia el nivel. Cada aprobada trae su ficha: n de pruebas, contaminación, pre-registro, madre y cupo | 2026-11-02 | `02-DOCS/reglas-de-medicion.md` |
| ¿Alcanza «avgR > 0» como criterio de holdout? | **No (Felipe, 2026-11-02).** TREND_4H con tope de 7 días pasó con +0.036, negativo sin sus 10 mejores y conservando el 15% del avgR de desarrollo. Desde ahora el holdout además debe aguantar costos ×1.5, no ser negativo sin las 10 mejores y conservar ≥ 1/3 del avgR de desarrollo | 2026-11-02 | `02-DOCS/reglas-de-medicion.md` |
| ¿Comprar/vender contra un salto de 1h con volumen anómalo (liquidaciones), con stop ancho, tiene edge neto de comisión? (`2026-11-03-reversion-salto-liquidaciones-1h`) | **RECHAZADA.** desarrollo n=1219 -0.185 [-0.242, -0.129]. No pasa: «avgR neto > 0 y ±2 EE fuera del cero» (-0.185 [-0.242, -0.129]); «tramos positivos ≥ 3» (0/4); «supera el percentil 95 del control nulo» (-0.185 vs p95 -0.018) | 2026-11-03 | `results/reports/2026-11-03-reversion-salto-liquidaciones-1h.md` |
| ¿TREND_1D con trailing en ATR real (desde la entrada, 2 ATR, tope 14 días) tiene edge neto dentro del alcance? (`2026-11-04-trend1d-trailing-atr-real-14d`) | **RECHAZADA.** desarrollo n=762 +0.049 [-0.027, +0.125]. No pasa: «avgR neto > 0 y ±2 EE fuera del cero» (+0.049 [-0.027, +0.125]); «concluyente (muestra, modelos, tramos)» (los tramos no coinciden en signo (2020-07-23:+0.22R 2021-10-22:-0.09R 2023-03-29:+0.08R 2024-06-18:-0.01R): depende del régimen; la dispersión entre tramos (0.30R) supera el doble del avgR (0.049R)); «tramos positivos ≥ 3» (2/4); «supera el percentil 95 del control nulo» (+0.049 vs p95 +0.082) | 2026-11-04 | `results/reports/2026-11-04-trend1d-trailing-atr-real-14d.md` |
