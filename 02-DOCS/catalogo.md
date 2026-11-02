# Catálogo de estrategias conocidas

Lo mantiene el **explorador** (`.claude/agents/explorador.md`), una vez por semana. Es la memoria de
lo que el mundo ya documentó o probó: de acá salen las ideas para `ideas.md`. Que una estrategia
esté acá **no** dice que funcione: dice qué evidencia hay y si vale la pena que la factory la mida.

**Evidencia:** A (fuera de muestra / replicada, con costos) · B (backtest público reproducible, o
efecto en varias fuentes) · C (competencia, ranking, pocos operadores en vivo: supervivencia) ·
D (anécdota, foro, sin metodología).

**Reglas:** resumen con palabras propias y link a la fuente; nunca código copiado ni texto de pago.

## Estrategias

| Estrategia | Mecanismo (¿quién pierde del otro lado?) | Fuente(s) | Evidencia | Mercado / TF | ¿Alcance? | ¿Ya probada? | ¿Sobrevive comisión? | Estado |
|---|---|---|---|---|---|---|---|---|
| Tendencia por canal (Donchian) | Las tendencias persisten porque la información se incorpora de a poco y los rezagados persiguen el precio | btc-signal-web (TREND_1D, TREND_4H) | B (propia: aprobada en desarrollo y holdout sin tope) | Cripto · 1d, 4h | Sólo si la mediana ≤ 7 días | Sí: ver `decisiones.md` | Sí en 1d (stop amplio) | Familia en revisión: se cierra si TREND_4H falla |
| Reversión a la media con stop | El precio vuelve tras excesos de corto plazo | btc-signal-web | B (propia, negativa) | Cripto/oro · intradía | Sí | Sí: rechazada (5 diseños) | — | Cerrada |

## Fuentes revisadas

| Fuente / tipo | Última revisión | Qué se sacó | Próxima vez |
|---|---|---|---|
| Papers y research (SSRN, arXiv q-fin, research cripto) | — | — | 1.ª semana |
| Repos y comunidades (Freqtrade, Jesse, QuantConnect) | — | — | 2.ª semana |
| Competencias y rankings (Kaggle, copy-trading Binance) | — | — | 3.ª semana |
| Libros y blogs con metodología | — | — | 4.ª semana |
