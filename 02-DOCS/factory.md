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
| 2. Validar contra resultados conocidos de btc-signal-web | en curso: paridad exacta con el script de TREND_1D hecha (tests); falta la corrida con datos reales (`validacion.yml`) |
| 3. Spec YAML + veredicto + workflows + dashboard en Pages | pendiente |
| 4. Rutina diaria | pendiente |
| 5. Contrato `approved.json` con btc-signal-web | pendiente |
