# Reglas de medición

Heredadas de btc-signal-web, cada una con el incidente que la justificó.

## Unidad: R
R = resultado / riesgo asumido al entrar (distancia entrada–stop). No se mueve con el tamaño de la
orden ni con el apalancamiento, así que es comparable en el tiempo y entre activos.

- `rBruto` = (salida − entrada) / riesgo × dirección
- `feeR` = comisión por lado × 2 × entrada / riesgo
- `rNeto` = `rBruto` − `feeR` ← **esto decide**

La comisión en R depende del tamaño del stop: SWING_1D con stop de 2.88% paga 0.034R; un scalp de
5m con stop de 0.47% paga ~0.2R y murió por eso. La frontera no es la temporalidad, es cuánto pesa
la comisión sobre el stop.

## Llenado: dos modelos
Dentro de una vela no se sabe si tocó primero el stop o el objetivo.
- **conservador**: el adverso primero. Es el que se reporta.
- **optimista**: el favorable primero. La diferencia entre los dos es la incertidumbre
  irreducible del backtest; si es grande, el resultado no es concluyente.

Si la vela abre más allá del stop (gap), se sale a la apertura, no al stop.

**Deslizamiento ≠ compuerta.** Hasta el 2026-10-11 btc-signal-web usaba el mismo parámetro para
decidir qué operaciones eran elegibles y a qué precio entraban; eso descartaba justo las que van
derecho al stop y sesgaba todo a favor. Aquí el deslizamiento sólo mueve el precio de entrada.

## Holdout
Fijo en **2025-09-09** (no relativo a hoy). Desarrollo = antes; holdout = desde ahí. Se mira una
vez, sobre la candidata final. Una corrida que cruza el corte es "mixto" y no valida nada.

Incidente: un `dias=365` relativo a la fecha de corrida cubría justo el período que horas después
pasó a ser holdout; dos "resultados contradictorios" eran la misma ventana.

## Concluyente
Mismas reglas que `btc-signal-web/src/lib/backtest/metrics.ts` (implementadas en `bt.metrics`).
Un resultado **no** es concluyente si pasa cualquiera de estas:
- Menos de 10 trades resueltos.
- La brecha entre modelo optimista y conservador es mayor que el propio avgR (el signo lo decide
  un supuesto sobre el orden intra-vela, no los datos).
- Los tramos temporales (2 a 4; cuentan los que tienen ≥ 3 trades) no coinciden en signo.
- La dispersión entre tramos supera el doble del avgR global.

Y aun siendo concluyente, sólo se aprueba si el **intervalo ±2 EE excluye el cero** y se cumple
el criterio pre-registrado.

## Criterio de holdout (endurecido el 2026-11-02)
Pasar el holdout con «avgR > 0» resultó demasiado fácil: `2026-11-02-trend4h-tope-7d` se aprobó con
+0.036 en holdout, el intervalo en el cero, negativo sin sus 10 mejores operaciones y conservando
sólo el 15% del avgR de desarrollo. Desde ahora, por defecto, el holdout además tiene que:
- **aguantar costos ×1.5** (avgR > 0);
- **no depender de pocas operaciones** (sin las 10 mejores, avgR ≥ 0);
- **conservar al menos 1/3 del avgR de desarrollo** (si se degrada más, era sobreajuste o un
  régimen que ya pasó).

Las specs pueden aflojar alguno sólo justificándolo en la hipótesis. Las evaluaciones ya hechas no
se re-evalúan.

## Dos niveles: aprobada y observación (desde 2026-11-02)

Pedido de btc-signal-web sobre la primera aprobada. Si pasa desarrollo:
- **APROBADA** (`nivel: aprobada`): el holdout cumple todos los criterios estrictos **y** no está
  contaminado. Es la única candidata a real (decisión de Felipe, después del paper).
- **OBSERVACION** (`nivel: observacion`): holdout positivo pero falla algún criterio estricto, o
  contaminado. Entra a `approved.json` sólo para paper: se observa, no se concluye.
- **RECHAZADA**: holdout sin operaciones o con avgR neto ≤ 0.

**Holdout contaminado:** la spec lo declara (`holdout_contaminado: true`) o la evaluación lo deduce
(otra de la misma `familia` ya miró el holdout). Una variante de algo ya mirado necesita otra
evidencia: nunca pasa de observación con ese holdout.

**La ficha** que acompaña cada aprobada u observación (reporte y `approved.json`): `n_pruebas` y
`variantes` de la familia, `holdout_contaminado`, `preregistro` (commit y fecha en que la spec entró
al repo, verificable contra la fecha de la evaluación), peor caída en R por tramo, el cupo
(`max_por_direccion`) y, si tiene `madre`, la comparación en el mismo período y tokens (diferencia de
avgR con ±2 EE —conservador: suma varianzas aunque las muestras se solapan— y la peor caída de cada
una). El auditor avisa si falta algo.

**Cupo de cartera:** `config.max_por_direccion` simula el tope del bot (posiciones abiertas por
dirección entre todos los símbolos, en orden de tiempo y de símbolo). Aproximación: cada símbolo se
simula por separado, así que una señal descartada por el cupo no libera ese símbolo para otra.

## Control nulo
Cuando aplique, comparar contra entradas al azar con la misma frecuencia y salida (TREND_1D en oro
se rechazó porque el azar rendía más que la regla).

## La brecha simulado-vs-vivo
Al 2026-10-11, producción de btc-signal-web: 91 trades, −0.332R, mientras el backtest daba ~0.
Deslizamiento y cooldowns ya descartados como causa. Hasta explicarla, un backtest positivo es
condición necesaria, no suficiente: por eso lo aprobado pasa primero por paper.
