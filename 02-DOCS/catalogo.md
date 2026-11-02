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
| Momentum intradía de series de tiempo (primera media hora predice la última) | Provisión de liquidez: quien cubre inventario al cierre empuja en la dirección de la primera media hora; pierde el que ofrece liquidez a destiempo | [Shen, Urquhart & Wang, Financial Review 2022](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/) | B (efecto con muestra dentro y fuera, sin verificar costos: no pude leer el texto) | BTC · 30m, trade de 30 min | Sí (borde: duración mínima) | No | Dudosa: movimiento esperado de media hora ≈ comisión de 0.1% | Propuesta |
| Estacionalidad por hora UTC (comprar ~21:00, vender ~23:00) | Retornos concentrados en la noche UTC (flujos de sesión americana/cierre); quién pierde no está claro | [Quantpedia, resumen de Padyšák y Vojtko](https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin); en contra: [UWA, 2017](https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/) (sin patrón persistente) | C (backtest de los autores vía resumen secundario; evidencia contradictoria) | BTC · 1h, trade de 2 h | Sí | **Sí: btc-signal-web 2026-10-20, NO** (ninguna hora paga la comisión) | Dudosa: 2 h de drift vs 0.1% ida y vuelta | Propuesta |
| Reversión/momentum por sesión (día vs noche) con regla condicional | Reversión de sobrerreacción diurna y deriva nocturna; el rezagado paga | [MDPI JRFM 19(9):692, Kraken horario 2016–2025](https://www.mdpi.com/1911-8074/19/9/692); [Quantpedia: sesiones nocturnas](https://quantpedia.com/how-to-profitably-trade-bitcoins-overnight-sessions/?a=6080) | C (la regla de BTC elegida en 2016–2020 rinde menos que comprar y mantener en 2021–2025: el propio paper la debilita) | BTC/ETH · 1h | Sí | No | Incierta | Propuesta (con cautela) |
| Reversión de retorno diario previo (por liquidez) | Sobrerreacción de corto plazo; en las monedas más líquidas domina el momentum, no la reversión | [Up or down? IRFA 78, 2021](https://earsiv.medeniyet.edu.tr/items/23a96c9f-3952-4bdf-aec5-abafb3aaab70); [Kozlowski et al., Applied Economics Letters 2021](https://ideas.repec.org/a/taf/apeclt/v28y2021i11p887-893.html) | B (varias fuentes, pero 2015–2019 y monedas chicas) | Cripto · 1d | Sí | Parcial: reversión con stop rechazada (5 diseños) | Dudosa en monedas grandes | Descartada por ahora: familia cerrada sin mecanismo nuevo |
| Carry de funding / basis (spot largo + perp corto) | Los apalancados largos pagan funding a quien toma el otro lado | [He & Manela, Fundamentals of Perpetual Futures](https://arxiv.org/abs/2212.06888): Sharpe ~1.8 con costos minoristas | B (sin verificar replicación) | BTC y alts · perp+spot | No: posición cubierta de semanas, y el motor es de un solo activo | No | — | Fuera de alcance/motor |
| Funding extremo como señal direccional contraria (extrapolación mía) | Funding muy alto = largos saturados y propensos a liquidación; el cascade los barre | Sin paper directo; contexto: [Lim 2026 sobre el 10-oct-2025](https://journals.lincoln.ac.nz/index.php/JFDA/article/view/1395); [Garcia Seuma 2026](https://arxiv.org/pdf/2607.27070) (las señales de alerta no predicen caídas individuales) | D | Perps USDⓈ-M · 1h–4h | Sí | **Sí: btc-signal-web 2026-10-20, NO** (el funding alto anuncia continuación, no giro) | Probable (stops amplios) | Descartada |
| Momentum de series de tiempo diario en cripto | Tendencia por reacción lenta; el tamaño de la comisión mata a muchas carteras | [Han, Kang & Ryu](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf): TSM fuerte, cross-section débil | B | Cripto · 1d | Sólo con tope ≤ 7 d | Sí: familia tendencia | — | En espera de TREND_4H; no entra a la cola |
| Compresión de volatilidad + ruptura (NR4 con razón vol 6d/100d < 0.5) | La volatilidad se agrupa; la compresión precede a la expansión | [CryptoDataDownload](https://www.cryptodatadownload.com/blog/posts/inside-contraction-historical-volatility-strategy/) | D (blog sin validación) | Cripto · 1d | Sí | Parcial: familia ruptura | — | Sólo catálogo |
| Reversión tras liquidaciones en cascada | Venta forzada deja precios por debajo del valor y la liquidez se recupera en horas | [Lim 2026](https://journals.lincoln.ac.nz/index.php/JFDA/article/view/1395): recuperación de liquidez intradía | D (no hay prueba de retornos explotables) | Perps · 5m–1h | Sí | No | Incierta | Sólo catálogo |

## Fuentes revisadas

| Fuente / tipo | Última revisión | Qué se sacó | Próxima vez |
|---|---|---|---|
| Papers y research (SSRN, arXiv q-fin, research cripto) | 2026-11-02 | 9 filas. Sólo resúmenes de búsqueda: arxiv.org, quantpedia.com y universidades no resolvieron en la sesión (hay que permitirlos en la red). Evidencia calificada con cautela, sin texto completo | Repetir con acceso a los textos para confirmar A/B |
| Repos y comunidades (Freqtrade, Jesse, QuantConnect) | — | — | 2.ª semana |
| Competencias y rankings (Kaggle, copy-trading Binance) | — | — | 3.ª semana |
| Libros y blogs con metodología | — | — | 4.ª semana |
