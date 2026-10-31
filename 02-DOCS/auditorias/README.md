# Auditorías del proceso

Informes del **auditor con criterio** (`.claude/agents/auditor.md`), uno por archivo
`AAAA-MM-DD.md`. Parte del informe del auditor determinista (`python -m bt.auditoria`, que corre en
el CI y aparece en el dashboard) y agrega lo que el código no puede juzgar: calidad de hipótesis,
criterios demasiado permisivos, variantes repetidas, lectura de resultados. Cada informe propone
como mucho 5 mejoras y hace seguimiento de las de la auditoría anterior.

Felipe decide qué mejoras se implementan. Las que sean verificables con código pasan a ser chequeos
nuevos de `bt.auditoria`.
