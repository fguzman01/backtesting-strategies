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

## 7. Horario y presupuesto [proyecto]

Plan de Claude: $20. Sesiones por día y semana (cada fila es una rutina):

| Hora (Chile) | Rol | Sesiones |
|---|---|---|
| 03:37 diario | Investigador (factory) | 1 |
| 06:00 diario | Analista liviano | 1 (corta) |
| 07:00 diario | Diseñador | 1 (corta, sólo si hay `aprobada`) |
| 08:00 diario | Desarrollador | 1 (sólo si hay `diseñada` aprobada) |
| 09–21 cada hora | Atención de pedidos | sólo si hay pedidos nuevos |
| 21:00 diario | Cronista | 0 (Actions) |
| Sábado 04:23 | Explorador | 1 |
| Domingo 05:13 / 07:47 | Auditor + puente / Analista semanal | 2 |

**Una tarea de desarrollo por día** (decisión de Felipe, 2026-11-06). Las rutinas que no encuentran
trabajo terminan sin abrir sesión larga.

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
- **Dónde corre:** a decidir entre Cloudflare Worker (gratis, sin servidor) y Railway (como el bot).

## 9. Plan de implementación [proyecto]

| Fase | Qué | Hecho cuando |
|---|---|---|
| 1 | Etiquetas en GitHub; migrar `backlog.md` a issues; `backlog.md` pasa a generarse | Los B-xx pendientes son issues; el resumen los lee de ahí (**código hecho 2026-11-06**: `.operador.yml`, `etiquetas.yml`, `bt.backlog`, `backlog.yml`, PO con issues) |
| 2 | Operador mínimo: grupo nuevo, tarjetas de propuesta y PR con ✅/❌, pedidos como issues | Aprobar #N desde Telegram cambia su etiqueta; un mensaje libre abre un issue |
| 3 | Diseñador, desarrollador y revisor de código como rutinas, más el liberador | Un issue aprobado llega a PR sin sesión manual |
| 4 | Atención de pedidos y cronista | Un pedido escrito a las 10:00 tiene plan en el grupo antes de las 12:00 |
| 5 | Copiar el marco a btc-signal-web y Sitbox (`OPERACION.md` + `.operador.yml`) | Cada uno con su grupo y su ciclo diario |

## 10. Preguntas abiertas

- ¿Cloudflare Worker o Railway para el operador?
- ¿Horario activo de la atención de pedidos (09–21 está propuesto)?
- ¿El cronista manda todos los días, o sólo cuando hubo movimiento?
- ¿Qué pasa con una tarjeta sin respuesta? Propuesta: se recuerda en el cierre del día y no vence.
