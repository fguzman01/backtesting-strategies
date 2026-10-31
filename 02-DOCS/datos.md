# Datos

## Fuente
**data.binance.vision** — zips mensuales oficiales de Binance (más los diarios del mes en curso).
Bajar dos años de velas de 1m por la API REST tarda horas; por zips, minutos. Es la misma fuente
que usa btc-signal-web (`scripts/bajar-klines-vision.py`).

| Mercado | Ruta base | Uso |
|---|---|---|
| Futuros USDⓈ-M | `data/futures/um` | default; lo que opera el bot |
| Spot | `data/spot` | activos sin historia en futuros (p. ej. PAXGUSDT, 6 años) |

## Formato local
`data/klines/<MERCADO>-<SIMBOLO>-<INTERVALO>.csv` con columnas `time,open,high,low,close,volume`
(`time` = apertura de la vela en ms UTC). No va a git; se reconstruye con:

```bash
python -m bt.data BTCUSDT 1d 2020-01
python -m bt.data PAXGUSDT 1d 2020-01 --mercado spot
```

## Cuidados
- Los zips de spot desde 2025 traen timestamps en microsegundos; `bt.data` los normaliza a ms.
- Un símbolo que empieza a listar después de la fecha pedida trunca la ventana: el reporte debe
  decir la ventana **efectiva**, no la pedida.
- Funding (futuros): `python -m bt.data <SIM> 1d 2020-01 --funding` lo baja a
  `data/funding/<SIM>.csv` y `bt.run --funding` lo cobra. En estrategias de varios días importa:
  en TREND_1D pesó −0.076R por operación en desarrollo.
