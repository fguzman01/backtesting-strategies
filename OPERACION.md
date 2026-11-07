# OPERACION.md — Marco de operación autónoma

> **Borrador para revisar (2026-11-06).** Es el marco que Felipe va a usar en todos sus proyectos
> con IA (esta factory, btc-signal-web, Sitbox). Esta primera versión se escribe acá porque es el
> proyecto más ordenado. Las partes **[marco]** se copian tal cual a otro proyecto; las
> **[proyecto]** se completan en cada uno.

## 1. El problema [marco]

Si Felipe no se conecta, el proyecto sólo avanza en lo que ya está automatizado. Las decisiones se
acumulan y el desarrollo del sistema mismo se detiene. **Objetivo:** que el proyecto avance todos
los días solo y que Felipe dirija desde un grupo de Telegram del proyecto, aprobando, rechazando o
pidiendo, sin abrir GitHub ni una sesión.

## 1b. Lo que ya existe y se reutiliza [marco]

btc-signal-web ya corre una primera versión de esto desde el 2026-11-04 (`rutinas/equipo.md` en su
rama `dev`): desarrollador a las 00:00 y a las 09:00, QA a las 20:00, informe diario a las 22:00 con ✅
por Telegram, arquitecto los domingos y PO los lunes. Este marco **generaliza lo que ahí funciona**
en vez de inventar algo paralelo:
- **Un solo mensaje por día con lo que espera decisión**, más avisos sólo si algo se rompe.
- **Una idea a la vez:** no se toma una nueva mientras haya otra trabada.
- **Sólo tareas S o M;** lo grande se parte.
- **QA no es quien desarrolló.**
- **Lo que toca dinero real queda en «requiere sesión».**

Lo que agrega: GitHub Issues como tablero en vez de un `BACKLOG.md` a mano, un operador reutilizable
entre proyectos y los pedidos en texto libre desde el grupo.

## 2. Principios [marco]

1. **Felipe decide, los agentes proponen y ejecutan.** Nada que toque código del sistema, dinero o
   producción pasa sin su ✅.
2. **Una sola fuente de tareas: GitHub Issues.** Cada mejora, pedido o bug es un issue; su estado
   son sus etiquetas. Los documentos (`backlog.md`, el resumen) son vistas generadas.
3. **Todo deja rastro en el repo:** quién propuso, quién aprobó, qué PR lo implementó.
4. **Presupuesto fijo:** cuántas sesiones de Claude por día está escrito acá (§7). El marco no lo excede.
5. **Si no hay nada de valor, no se inventa trabajo.** Un día sin tarjetas es un resultado válido.
6. **Contexto limpio para revisar:** quien revisa nunca es quien escribió.

## 3. Ciclo de vida de una tarea [marco]

```
propuesta ──✅──► aprobada ──► diseñada ──✅──► en-curso ──► en-revision ──✅──► hecha
    │                              │                              │
    └──❌──► descartada            └──❌──► (vuelve a aprobada,    └──❌──► (vuelve a en-curso
                                             con el comentario)              con el comentario)
```

Etiquetas de GitHub (prefijo por grupo):

| Grupo | Etiquetas |
|---|---|
| `estado:` | `propuesta`, `aprobada`, `diseñada`, `en-curso`, `en-revision`, `hecha`, `descartada` |
| `tipo:` | `mejora`, `pedido` (lo escribió Felipe), `bug`, `investigacion` |
| `prio:` | `P1` (confianza o destraba), `P2` (ahorra trabajo), `P3` (conveniente) |
| `riesgo:` | `bajo` (docs, datos), `medio` (código con tests), `alto` (workflows, contrato, dinero, producción) |

Cada issue trae: **problema**, **hecho cuando** (verificable), **costo** (sesiones de Claude, Actions)
y, al pasar a `diseñada`, el **plan** como comentario.

## 4. Roles [marco con nombres del proyecto]

| Rol | Qué hace | Cuándo | Sale con |
|---|---|---|---|
| **Analista** (PO) | Junta mejoras (auditor, CI, retroalimentación, avisos repetidos) y abre issues `propuesta` con problema, hecho-cuando y costo. Prioriza | Diario 06:00 (liviano); semanal domingo (completo) | Issues + tarjetas ✅/❌ |
| **Diseñador** | Para el issue `aprobada` de mayor prioridad: plan corto (archivos, test, riesgo, cómo se revierte) | Diario 07:00 | Comentario `plan` + tarjeta ✅/❌ |
| **Desarrollador** | Implementa UN issue `diseñada` aprobado: rama, código, tests, PR con "closes #N" | Diario 08:00 | PR + issue `en-revision` |
| **Revisor de código** | Contexto limpio: lee el PR contra el plan y el hecho-cuando; bugs, tests faltantes, alcance de más | Al abrir el PR | Comentario en el PR (ok / cambios) |
| **Tester** | CI, auditor determinista y chequeos del proyecto | En cada PR (Actions, sin tokens) | Estado del PR |
| **Liberador** | Fusiona lo permitido sin ✅ (§6); lo demás lo manda a Telegram con [Fusionar] / [Rechazar] | Al pasar CI y revisión | Merge o tarjeta |
| **Atención de pedidos** | Toma issues `tipo:pedido` (mensajes de Felipe), responde con un plan (vuelve al ciclo en `diseñada`) o con la respuesta si era una pregunta | Cada hora en horario activo | Respuesta en el grupo |
| **Cronista** | Cierre del día: qué avanzó, qué espera decisión, qué viene mañana | Diario 21:00 (sin tokens) | Mensaje en el grupo |

**[proyecto] Roles propios de la factory** (siguen como están): investigador (diario), explorador
(sábado), auditor + puente (domingo), revisor de sesgos (en cada spec), evaluar / adelante / cartera
(Actions). El analista toma sus hallazgos como fuente.

## 5. El grupo de Telegram [marco]

Un grupo por proyecto, con un bot (el **operador**). Tipos de mensaje:

| Mensaje | Ejemplo | Botones |
|---|---|---|
| Propuesta | «#51 Simulador de cartera — P2, riesgo medio, 1 sesión» | ✅ Aprobar · ❌ Descartar · 💬 Comentar |
| Plan | «#51 plan: `bt/cartera.py` + test; revierte borrando el módulo» | ✅ Implementar · ❌ Rehacer |
| PR listo | «PR #60 cierra #51 — CI ✅, revisor ok, +180 −4» | ✅ Fusionar · ❌ Rechazar · 🔗 Ver |
| Aviso | «evaluar falló dos veces seguidas: …» | 🔗 Ver |
| Cierre del día | resumen | — |

- Un **mensaje libre** de Felipe abre un issue `tipo:pedido` con su texto. El bot responde «anotado
  #N, lo tomo en la próxima corrida».
- **Responder a una tarjeta** con texto deja ese texto como comentario del issue o PR. Si la tarjeta
  era de ❌, el texto es el motivo.
- Sólo Felipe puede aprobar: el operador ignora botones y mensajes de cualquier otro usuario.

## 6. Qué pasa solo y qué pide ✅ [marco + proyecto]

| Pasa solo | Pide ✅ de Felipe | Nunca sin Felipe, fuera de este canal |
|---|---|---|
| `riesgo:bajo`: docs, cola de ideas, catálogo, backlog generado; **[proyecto]** specs con revisión de sesgos no bloqueada, resultados de evaluaciones rechazadas | Todo código del sistema, workflows, `approved.json` **[proyecto]**, despliegues, cambios de reglas de medición | Dinero real (encender el real bot, cambiar tamaños) **[proyecto]** |

## 7. Horario y presupuesto [cuenta completa]

Todas las rutinas de la cuenta comparten el mismo plan de Claude ($20): ventanas de uso de 5 horas
que empiezan con la primera sesión, más un tope semanal. Un horario nuevo se decide mirando la
cuenta completa, no un proyecto. Ocupación al 2026-11-06 (hora de Chile):

| Ventana (aprox.) | Qué corre hoy | Carga |
|---|---|---|
| 20:00–01:00 | QA btc 20:00 (opus) · informe btc 22:00 (opus) · desarrollador btc 00:00 (opus) | **alta** |
| 01:00–03:30 | — | libre |
| **03:37–08:37** | investigador factory 03:37 · Seedbox analista 08:23; sáb. explorador 04:23; dom. auditor 05:13 y PO factory 07:47 | **baja entre semana** |
| 09:00–14:00 | desarrollador btc 09:00 (sonnet); lun. PO btc 10:00 (opus); sesiones de Felipe | media |
| 14:00–20:00 | sesiones de Felipe; dom. arquitecto btc 18:00 (opus) | la usa Felipe |

**Propuesta para la factory:** todo el ciclo nuevo en la ventana de la madrugada, que es la más libre y
termina antes de que Felipe despierte. Las tarjetas lo esperan en la mañana.

| Hora (Chile) | Rol | Modelo | Corre sólo si |
|---|---|---|---|
| 03:37 | Investigador (ya existe) | el de siempre | — |
| 04:45 y 19:45 | Diseñador + atención de pedidos (`disenador.md`) | sonnet | hay un issue `aprobada` (mejoras aprobadas y pedidos) |
| 05:15 (lun–vie) | Desarrollador + revisor de código (`desarrollador.md`, `revisor-codigo.md`) | el de siempre | hay un issue `en-curso` (plan aprobado) y nada trabado |
| 21:00 | Cronista | — (Actions) | hubo movimiento o hay decisiones pendientes |

- **El analista diario no se creó:** el PO semanal (domingo) alcanza por ahora; se suma si el backlog se queda corto.
- **Pedidos dos veces al día, no cada hora:** cada hora abriría ventanas en el horario de Felipe y gastaría
  sin necesidad. Algo urgente se pide en una sesión.
- **Fines de semana:** el sábado y el domingo la madrugada ya trae explorador, auditor y PO. El
  desarrollador de la factory no corre esos días.
- **Una tarea de desarrollo por día** (decisión de Felipe, 2026-11-06).
- **A revisar después de una semana** en la página de uso de Claude: si el tope semanal aprieta,
  primero se pasa a sonnet lo que hoy corre en opus en btc-signal-web y no escribe código (informe, QA).

## 8. El operador [marco]

Servicio propio y chico, reutilizable en todos los proyectos (decisión de Felipe, 2026-11-06):

- **Recibe** el webhook de Telegram: botones y mensajes. Los traduce a la API de GitHub: etiquetas,
  comentarios, merge, cierre, issues nuevos. Valida que el usuario sea Felipe y que la tarjeta no
  haya vencido.
- **Envía**: las rutinas y los workflows le mandan tarjetas a un endpoint del operador, con una
  clave, o directo a Telegram cuando no hay botones.
- **Configuración por repo** en `.operador.yml`: grupo de Telegram, etiquetas, qué pasa solo y qué
  pide ✅.
- **Sin estado propio:** el estado vive en GitHub (etiquetas, comentarios). Si el operador se cae,
  no se pierde nada.
- **Dónde corre:** un servicio propio en **Railway**, en la nube que ya se usa (decisión de Felipe,
  2026-11-06). btc-signal-web ya resuelve el webhook de Telegram y el merge por la API de GitHub
  (`lib/ops/despliegue.ts`, `/api/telegram`): el operador nace de ese código, generalizado.

## 9. Plan de implementación [proyecto]

| Fase | Qué | Hecho cuando |
|---|---|---|
| 1 | Etiquetas en GitHub; migrar `backlog.md` a issues; `backlog.md` pasa a generarse | Los B-xx pendientes son issues; el resumen los lee de ahí (**código hecho 2026-11-06**: `.operador.yml`, `etiquetas.yml`, `bt.backlog`, `backlog.yml`, PO con issues) |
| 2 | Operador mínimo: grupo nuevo, tarjetas de propuesta y PR con ✅/❌, pedidos como issues | Aprobar #N desde Telegram cambia su etiqueta; un mensaje libre abre un issue (**hecho 2026-11-06**: fguzman01/operador en Railway, grupo «Factory · Operación», pedido #49; tarjetas `tarjetas.yml` y cierre `cierre.yml`) |
| 3 | Diseñador, desarrollador y revisor de código como rutinas, más el liberador | Un issue aprobado llega a PR sin sesión manual (**código hecho 2026-11-08**: agentes `disenador`, `desarrollador`, `revisor-codigo`; el liberador son las tarjetas de PR + auto-merge) |
| 4 | Atención de pedidos y cronista | Un pedido tiene plan en el grupo en la siguiente corrida del diseñador (04:45 o 19:45) (**hecho 2026-11-08**: el diseñador atiende los pedidos; respuestas con `<!-- telegram -->` llegan al grupo; el cierre reenvía las tarjetas pendientes) |
| 5 | Copiar el marco a btc-signal-web y Sitbox (`OPERACION.md` + `.operador.yml`) | Cada uno con su grupo y su ciclo diario |

## 10. Decisiones tomadas (2026-11-06)

- **Tareas:** GitHub Issues.
- **Operador:** servicio propio reutilizable, en Railway.
- **Ritmo:** una tarea de desarrollo por día.
- **Autonomía:** sólo pasa solo lo de bajo riesgo, como hoy.
- **Pedidos:** se vuelven issues y se toman en la siguiente corrida.
- **Tarjetas sin respuesta:** no vencen y se recuerdan en el cierre del día.
- **Horario:** el ciclo de la factory corre en la ventana de la madrugada (§7). Confirmado por Felipe.
- **Cierre del día:** sólo si hubo movimiento o hay decisiones pendientes. Confirmado por Felipe.
