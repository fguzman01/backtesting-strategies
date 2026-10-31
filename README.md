# backtesting-strategies

Factory de backtesting: entra una idea de estrategia, sale un veredicto auditable contra un
criterio escrito antes de correr. Lo aprobado alimenta a
[btc-signal-web](https://github.com/fguzman01/btc-signal-web) para paper y luego real.
Meta: **una estrategia evaluada por día**.

- Reglas para agentes: [`CLAUDE.md`](CLAUDE.md)
- Diseño de la factory y estado por fase: [`02-DOCS/factory.md`](02-DOCS/factory.md)
- Lo que ya se midió (leer antes de proponer): [`02-DOCS/decisiones.md`](02-DOCS/decisiones.md)

## Uso

```bash
pip install -e '.[dev]'
pytest
python -m bt.data BTCUSDT 1d 2020-01
python -m bt.run donchian_breakout BTCUSDT 1d --desde 2020-01-01 --nota "prueba"
```

O desde GitHub: **Actions → backtest-manual → Run workflow**.

## Cómo se evalúa una estrategia

1. Copiar `specs/PLANTILLA.yaml` a `specs/<AAAA-MM-DD-slug>.yaml`, completar y poner
   `estado: pre-registrada`.
2. Al llegar a `main`, el workflow **evaluar** la corre. Rechazadas van directo a `main`;
   aprobadas abren un PR que agrega la estrategia a `results/approved.json`.
3. Resultados en `results/reports/` y en el dashboard de GitHub Pages.
