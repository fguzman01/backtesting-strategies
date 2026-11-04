# Backlog del sistema

Mejoras y desarrollo nuevo de **la factory misma** (no estrategias: esas van en `ideas.md`). Lo
mantiene el **PO** (`.claude/agents/po.md`) cada domingo; Felipe decide qué se hace.

**Estados:** `propuesta` (la escribió el PO) · `aprobada` (Felipe dijo que sí) · `en curso` ·
`hecha` (con el PR) · `descartada` (con el motivo).
**Prioridad:** P1 sube la confianza en lo que sale de la factory o destraba algo · P2 ahorra trabajo a
Felipe o al sistema · P3 conveniente.
**Costo:** en tokens de Claude (lo escaso, plan de $20) y en tiempo de Actions (gratis).

## Recomendadas para esta semana

Las elige el PO: como mucho 3, ordenadas. El resumen del lunes por Telegram las muestra.

1. **B-01** Simulador de cartera
2. **B-02** Corrección por número de pruebas
3. **B-05** Medir TREND_4H_T7 sin sesgo de supervivencia

## Pendientes

| ID | Mejora | Origen | Problema que resuelve / valor | Hecho cuando | Costo | Prio | Estado |
|---|---|---|---|---|---|---|---|
| B-01 | Simulador de cartera | Mapa de la factory (2026-11-02) | Con 2+ aprobadas, ver cómo se comportan JUNTAS: correlación, peor caída de la cartera con el presupuesto de riesgo y el cupo del bot. Hoy cada una se mide sola | `bt.cartera` simula las aprobadas juntas en la misma ventana; reporte con peor caída y correlación; test | 1 sesión · Actions | P2 (P1 cuando haya 2 aprobadas) | en curso (Felipe, 2026-11-04) |
| B-02 | Corrección por número de pruebas | Mapa de la factory | Con muchas pruebas alguna pasa por azar. El auditor sólo cuenta; no endurece el criterio a medida que crece `n_pruebas` | El criterio de desarrollo exige más (p. ej. Bonferroni/Holm sobre el IC, o Sharpe deflactado) según las pruebas de la familia; documentado en reglas-de-medicion.md; test | 1 sesión | P1 | en curso (Felipe, 2026-11-04) |
| B-03 | Revisor de sesgos de cada spec | `factory.md` (descrito, nunca corrió) | Una spec floja o una idea repetida llega al PR sin que nadie la critique; el CI sólo valida forma | Subagente con contexto limpio en el paso 3 del investigador; deja su crítica en el PR; si encuentra un problema grave, la spec no se fusiona sola | +20% de tokens por spec | P2 | en curso (Felipe, 2026-11-04) |
| B-04 | Dashboard ampliado | Mapa de la factory | El sitio sólo muestra evaluaciones; la cola, el catálogo, el paper, la prueba hacia adelante y el backlog hay que leerlos en GitHub | `bt.sitio` agrega secciones para cola, adelante, retroalimentación y backlog; test | 1 sesión · Actions | P3 | en curso (Felipe, 2026-11-04) |
| B-05 | Medir TREND_4H_T7 sin sesgo de supervivencia | PR #25 | Se aprobó con 14 tokens que siguen vivos; no sabemos cuánto de su edge es supervivencia | Spec nueva pre-registrada con `universo.dinamico` (holdout contaminado: es informativa) evaluada; línea en decisiones.md | 1 spec (rutina) · Actions | P1 | hecha (2026-11-04): el sesgo explicaba ~1/3 del edge; ver decisiones.md |
| B-06 | Motor intrabar para scalps (5m–30m) | btc-signal-web (2026-10-13) | Sin modelar lo que pasa dentro de la vela, el backtest de scalp sale optimista; la factory no puede evaluar scalps con fidelidad | `bt.engine` con modo intrabar (velas de 1m para resolver stop/objetivo) y paridad con el modo intrabar del bot; test | 1–2 sesiones | P2 (P1 si llega una idea de scalp) | propuesta |
| B-07 | Fijar el umbral de estabilidad | PR #26 | La estabilidad de parámetros hoy sólo informa | Con 3+ evaluaciones medidas, proponer `estabilidad_minima` por defecto en la PLANTILLA (decisión de Felipe) | casi 0 | P2 | propuesta (esperar datos) |
| B-08 | Revisar la lista NO_CRIPTO del universo | PR #25 | La lista de acciones/ETF/materias primas es a mano; hay 3 dudosas (SPCX, DRAM, SNXX) y aparecen nuevas | El PO revisa cada mes los nuevos del top 50 de `results/universo/futures-usdt.json` y propone altas | casi 0 (rutina) | P3 | propuesta |

## Hechas

| ID | Mejora | PR | Cuándo |
|---|---|---|---|
| — | Chequeo de calidad de datos con criterio (auditoría 2026-11-01, mejora 1) | — | 2026-11-01 |
| — | Aviso de salidas por timeout (auditoría 2026-11-01, mejora 2) | — | 2026-11-01 |
| — | Trailing desde la entrada en el motor (auditoría 2026-11-01, mejora 4) | — | 2026-11-01 |
| — | Robustez: costos ×1.5 y sin las 10 mejores; historia con spot (auditoría 2026-11-01, mejora 5) | — | 2026-11-01 |
| — | Ficha: dos niveles, n de pruebas, holdout contaminado, pre-registro, madre, cupo | #20, #23 | 2026-11-02 |
| — | Retroalimentación automática con el bot (PR al bot, informe del paper, puente) | #21 | 2026-11-02 |
| — | Universo sin sesgo de supervivencia y prueba hacia adelante | #25 | 2026-11-03 |
| — | Estabilidad de parámetros | #26 | 2026-11-03 |
| — | Resumen semanal por Telegram | #27 | 2026-11-03 |

## Descartadas

| ID | Mejora | Motivo |
|---|---|---|
| — | Más exploradores | La mayoría de lo que encuentran es evidencia C y hay dominios bloqueados; más corridas no mejoran la cola (2026-11-02) |
