# La factory

Un proceso **repetible** (siempre el mismo camino) y **auditable** (cada paso deja rastro en el
repo). Adaptado de la idea de "AI Factory": sólo se quedan las etapas que aportan en backtesting.

```
Entrada ──► Spec (pre-registro) ──► Builder (TDD) ──► Revisión ──► Veredicto ──► ¿Humano? ──► main / PR
   ▲             │                      │               │             │
   └──── Brain (02-DOCS) se consulta antes de cada paso y se actualiza al cerrar ─────┘
```

| Etapa | Qué hace | Quién | Rastro |
|---|---|---|---|
| Entrada | Cola de ideas: issues con etiqueta `idea`, o las que propone la rutina diaria | Felipe / rutina | issue |
| Brain | Se consulta `alcance.md` (horizonte permitido) y `decisiones.md` para no repetir; se descarta lo ya probado | rutina | — |
| Spec | Hipótesis, reglas, universo, timeframe, ventana, **criterio de aprobación** | Claude | `specs/*.yaml` |
| Builder | `src/bt/strategies/<slug>.py` + test (incluye chequeo de look-ahead) | Claude | commit en rama |
| Revisión determinista | look-ahead, comisión aplicada, n mínimo, determinismo | CI (`bt.checks`) | log de Actions |
| Revisión de sesgos | Subagente con contexto limpio: overfitting, data snooping, supervivencia | Claude | comentario en el reporte |
| Veredicto | Desarrollo contra el criterio; sólo si pasa se mira el holdout, una vez | código (`bt.verdict`) | `results/reports/`, `mediciones.jsonl` |
| ¿Humano? | **Regla fija**: rechazos/no concluyentes → `main` directo. Aprobadas → PR que toca `approved.json` | código + Felipe | PR |
| Auditor determinista | 12 chequeos. Proceso: pre-registro antes de evaluar, holdout una vez y sólo si pasa desarrollo, `approved.json` coherente, test de look-ahead por estrategia, Brain al día, bitácora determinista, data snooping. Metodología: ventana y potencia estadística (años, 2022 bajista, ±2 EE vs comisión, n por tramo), calidad de datos, rechazos al borde, desgaste del holdout | CI (`bt.auditoria`) | resumen del CI, dashboard |
| Explorador | Investiga estrategias conocidas (papers, research cripto, repos, competencias, rankings), las documenta con su evidencia (A–D) y deja 5–7 por semana en la cola; las A/B dentro del alcance entran solas a `en cola` | Claude, semanal (`.claude/agents/explorador.md`) | `02-DOCS/catalogo.md`, `02-DOCS/ideas.md`, PR `[rutina]` |
| Auditor con criterio | Lo que el código no juzga: (1) proceso: hipótesis, criterios flojos, variantes repetidas; (2) metodología: ¿más o menos años?, supervivencia, costos realistas, robustez, nulo, renovación del holdout; (3) rechazadas: clasificarlas y proponer versiones con mecanismo nuevo (nunca re-evaluar); (4) paridad backtest ↔ bot real de btc-signal-web; (5) ≤ 5 mejoras | Claude, semanal (`.claude/agents/auditor.md`) | `02-DOCS/auditorias/`, `02-DOCS/ideas.md`, PR |

## Cómo corre (Fase 3)

1. Una spec llega a `main` con `estado: pre-registrada` (`specs/<id>.yaml`, validada por `bt.spec`).
2. `evaluar.yml` corre `python -m bt.evaluar --pendientes --bajar`: baja velas y funding, corre
   desarrollo, aplica el criterio (+ control nulo `bt.nulo` + alcance), y sólo si pasa mira el
   holdout. Escribe `results/evaluaciones/<id>.json`, `results/reports/<id>.md` y la bitácora.
3. Rechazada / no concluyente → commit directo a `main`. Aprobada → PR que agrega la estrategia a
   `results/approved.json`; Felipe revisa y hace merge.
4. `pages.yml` regenera el dashboard (`python -m bt.sitio`) en GitHub Pages.

### La rutina diaria (Fase 4)

- **Cuándo:** todos los días de madrugada, hora de Chile. El auditor, los domingos.
- **Qué hace** (`.claude/agents/investigador.md`): toma la primera idea `en cola` de
  `02-DOCS/ideas.md` → spec pre-registrada + estrategia + test (sin mirar datos reales) → PR
  `[rutina] ...`. Si no hay nada en cola, investiga y deja UNA idea `propuesta`; Felipe la pasa a
  `en cola` si le gusta.
- **Auto-merge** (`automerge.yml`): si el CI pasa y el PR sólo agrega specs/estrategias/tests nuevos
  o toca `ideas.md` (`scripts/rutas_automerge.py`), se fusiona solo y dispara `evaluar`. Cualquier
  otra ruta queda para Felipe. Lo aprobado sigue yendo a `approved.json` por un PR manual.

Una spec evaluada no se re-evalúa: la existencia de `results/evaluaciones/<id>.json` lo impide
(el holdout ya se miró). Para otra pregunta, otra spec con otro id.

## Qué se dejó afuera y por qué

- **Revisores de UX/UI/seguridad del video**: no hay producto de usuario que revisar.
- **Modelos de otras familias**: con el plan de $20 no se justifica. La independencia la dan el
  pre-registro y los chequeos deterministas, que no tienen sesgo de autor.
- **Agente que decide si interviene un humano**: es una regla en código. Lo que va a dinero real
  siempre pasa por Felipe.

## Presupuesto

Una sesión de Claude por día (Routine de Claude Code, usa la suscripción) para escribir spec +
estrategia + test. Todo el cómputo (bajar datos, correr, reportar, publicar) es GitHub Actions, sin
tokens.

## Estado por fase

| Fase | Estado |
|---|---|
| 0. Brain y fundaciones | hecha |
| 1. Motor determinista (datos, motor, métricas, holdout, bitácora, CLI) | hecha (versión mínima) |
| 2. Validar contra resultados conocidos de btc-signal-web | hecha: reproduce TREND_1D (14 tokens dev y holdout, oro dev) con datos reales, 2026-10-31 |
| 3. Spec YAML + veredicto + workflows + dashboard en Pages | hecha (2026-10-31); primera spec real: `2026-10-31-trend1d-tope-7d` |
| 3b. Auditor del proceso (determinista + agente con criterio) | hecho (2026-10-31); falta programar la rutina semanal del agente |
| 4. Rutina diaria + auditor semanal | código hecho (2026-10-31): agente `investigador`, auto-merge con rutas seguras. Falta crear las dos rutinas en la cuenta de Felipe |
| 4b. Explorador semanal (catálogo de estrategias conocidas → cola) | código hecho (2026-11-02); falta que Felipe agregue el repo a su rutina |
| 5. Contrato `approved.json` con btc-signal-web | pendiente |
