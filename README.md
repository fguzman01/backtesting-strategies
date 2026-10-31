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
