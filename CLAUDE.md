# CLAUDE.md — backtesting-strategies

Punto de entrada para cualquier agente que trabaje en este repo. Leelo completo antes de tocar nada.

## Qué es

Una **factory de backtesting**: entra una idea de estrategia, sale un veredicto auditable
(APROBADA / RECHAZADA / NO CONCLUYENTE) contra un criterio escrito **antes** de correr. Las
aprobadas pasan a `results/approved.json`, que consume `fguzman01/btc-signal-web` para operarlas en
paper y después en real. Objetivo de régimen: **una estrategia evaluada por día**.

Diseño completo de la factory: `02-DOCS/factory.md`.
**Qué estrategias se buscan (horizonte, activos, prioridad): `02-DOCS/alcance.md`.** Resumen:
cualquier tipo de estrategia que sea rentable, en cualquier activo operable en Binance, siempre
de scalp a diario (señal entre 5m y 1d, trades de horas a pocos días). Nada semanal ni de meses.

## Reglas (no sugerencias)

0. **Antes de proponer evaluar algo, buscá en `02-DOCS/decisiones.md`.** Está indexado por la
   pregunta. Lo que ya se midió no se vuelve a medir igual; una pregunta cerrada sólo se reabre con
   datos nuevos, más muestra o un mecanismo distinto. Al cerrar una pregunta, agregá una línea ahí.
1. **Pre-registro primero.** Ninguna corrida sin su spec en `specs/` con hipótesis, reglas,
   universo, ventana y criterio de aprobación. Cambiar el criterio después de ver el número
   invalida la evaluación.
2. **El holdout se mira una vez.** Corte fijo en `2025-09-09` (`bt.splits.HOLDOUT_DESDE`). El
   desarrollo no lo toca; el código recorta la ventana si no se pide explícitamente.
3. **Ningún avgR se cita sin su ventana y su config.** Un número sin ventana es una anécdota.
   Toda corrida queda registrada sola en `results/mediciones.jsonl` (`bt.bitacora`).
4. **Resultados en R, netos de comisión.** `avgRNeto` decide; el win rate es contexto.
5. **Sin look-ahead.** Una señal en la vela `t` sólo usa datos hasta el cierre de `t` y se ejecuta
   en la apertura de `t+1`. `bt.checks.chequear_lookahead` lo verifica; todo test de estrategia lo usa.
6. **Determinismo.** La misma spec sobre los mismos datos da el mismo número. Si no, es un bug.
7. **Lo que llega a dinero real lo aprueba Felipe.** Tocar `results/approved.json` siempre va por PR.

## Mapa

| Ruta | Qué |
|---|---|
| `02-DOCS/` | Brain: decisiones, reglas de medición, datos, diseño de la factory |
| `specs/` | Pre-registros (`AAAA-MM-DD-<slug>.yaml`) |
| `src/bt/data.py` | Descarga velas de data.binance.vision → `data/klines/` (fuera de git) |
| `src/bt/engine.py` | Simulador por barras, dos modelos de llenado (conservador / optimista) |
| `src/bt/metrics.py` | avgR, ±2 EE, tramos, concluyente |
| `src/bt/splits.py` | Holdout fijo |
| `src/bt/checks.py` | Chequeos anti-sesgo |
| `src/bt/bitacora.py` | Registro de corridas |
| `src/bt/run.py` | CLI: corre una estrategia y registra |
| `src/bt/strategies/` | Una estrategia por archivo, función `senales(df, **params)` |
| `results/` | `mediciones.jsonl`, reportes, `approved.json` |

## Comandos

```bash
pip install -e '.[dev]'
pytest
ruff check .
python -m bt.data BTCUSDT 1d 2020-01            # baja velas
python -m bt.run donchian_breakout BTCUSDT 1d --nota "prueba"
```

## Proyecto hermano

`fguzman01/btc-signal-web` tiene el motor original en TypeScript (`src/lib/backtest/`) y la
historia completa de mediciones (`DECISIONES.md`, `data/mediciones.jsonl`). Las convenciones de
este repo (R, comisión 0.05%/lado, llenado conservador, holdout 2025-09-09, esquema de la
bitácora) salen de ahí a propósito, para que los números sean comparables.
