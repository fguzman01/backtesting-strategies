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

## Historia extendida con spot (desde 2026-11-01)
Con `universo.historia_spot: true` en la spec, cada símbolo usa velas de **spot antes del primer día
con futuros** y de futuros desde ahí (`bt.data.cargar_extendida`). Agrega 2017-2019 (bajista de 2018,
lateral de 2019) donde el spot existe: BTC, ETH, BNB, LTC, XRP, TRX, ADA, LINK, DOGE. Los tokens
listados en 2020 (SOL, AVAX, NEAR, UNI, DOT) no ganan historia. Cuidados:
- En el tramo de spot no hay funding (los perpetuos no existían): es correcto, no un faltante.
- En la unión spot→futuro puede haber un salto chico por la base entre ambos mercados.
- Las specs evaluadas antes de esta opción no cambian (no se re-evalúan), y la validación contra
  btc-signal-web sigue usando sólo futuros.
