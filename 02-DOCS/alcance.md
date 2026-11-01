# Alcance: qué estrategias busca la factory

Definido con Felipe el 2026-10-31.

## Objetivo
**Encontrar estrategias rentables.** El tipo de estrategia no importa: tendencia, ruptura,
reversión, funding, momentum relativo, pares, estacionalidad, lo que sea. Lo que importa es que
pase el criterio pre-registrado, neto de comisión, en desarrollo y en holdout.

## Horizonte (esto sí es restricción)

| Sí | Temporalidad de la señal | Duración típica del trade |
|---|---|---|
| Scalp | 5m, 15m, 30m, 1h | minutos a horas |
| Swing | 1h, 4h | horas a pocos días |
| Diario | 1d | algunos días |

**No:** estrategias de largo plazo. Nada semanal (1w) ni mensual, nada de posiciones que
duren semanas o meses, nada de buy-and-hold.

Regla operativa (ajustable si Felipe lo pide):
- La señal se genera entre **5m y 1d**.
- La **duración mediana** del trade es de **7 días o menos**, y la spec debe fijar un
  `timeout_velas` que corte como máximo a los **14 días**.

Recordatorio de `decisiones.md`: en temporalidades chicas la comisión pesa mucho en R
(un stop de 0.47% paga ~0.2R). Una idea de scalp en 5m tiene que explicar por qué su edge bruto
supera eso.

## Activos
**Cualquier activo que se pueda operar en Binance** y tenga historia en data.binance.vision:
futuros USDⓈ-M primero (es lo que opera el bot) y spot cuando haga falta más historia
(p. ej. PAXG). Cripto es el punto de partida, pero no un límite: también entra cualquier otro
activo que Binance liste (oro, etc.).

## Prioridad en la fase inicial
Empezar por las familias que ya corre btc-signal-web, porque hay números con qué validar el motor
y el resultado se puede usar enseguida:
- SCALP en 15m / 30m / 1h (motor de tendencia)
- SWING_1H
- SWING_1D / diario (incluido oro)

Después se abre a otros tipos y activos. La rutina diaria alterna entre "mejorar o extender lo
conocido" (otros símbolos, otras temporalidades dentro del rango) e "idea nueva".

## Decisiones de alcance (Felipe)

- **2026-11-01 · Familia de tendencia diaria (TREND_1D y variantes).** El edge crece con la
  duración (+0.087 con tope de 7 días → +0.148 con 14 → +0.545 sin tope, ~22 días de media), así que
  con este alcance no pasa. **Se mantiene el alcance, sin excepción.** Se espera el resultado de
  TREND_4H con tope de 7 días (idea #2); si falla, **se cierra la familia de tendencia en la
  factory** y se buscan otros tipos de estrategia. TREND_1D sin tope sigue corriendo en paper en
  btc-signal-web, fuera de la factory.
- **2026-11-01 · Motor y datos.** Se aprueban (a) que el motor conozca la posición abierta para
  simular trailing desde la entrada, breakeven y salidas parciales TP1/TP2, como el bot real; y
  (b) más historia (spot 2017–2019 donde no hay futuros) y robustez automática en cada reporte
  (costos +50% y sin las 10 mejores operaciones).
