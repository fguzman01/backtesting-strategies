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
