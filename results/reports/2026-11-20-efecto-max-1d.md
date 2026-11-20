# 2026-11-20-efecto-max-1d — RECHAZADA

- **Estrategia:** `efecto_max` {"ventana": 30, "k": 3, "atr_n": 14, "stop_atr": 2.0, "trailing_atr": 2.0}
- **Universo:** futures · 1d · dinámico: los 20 más operados de cada mes, incluidos los retirados (202 símbolos en total)
- **Evaluada:** 2026-11-20T06:46:16+00:00 · commit `6755482`

## Hipótesis

Mecanismo: demanda por activos «lotería». Las monedas con una suba extrema reciente atraen atención y compradores minoristas que buscan el siguiente salto, y siguen unos días; quien pierde es el que vende a destiempo (o abre el corto contra la atención). La señal es el extremo (el mayor retorno diario de la ventana), no el retorno acumulado, así que no es el momentum de corte transversal ya cerrado (7 y 1 día, las dos ≈ 0).
Regla, UNA sola configuración fijada antes de correr y tomada de la fuente, no de datos: cada vela diaria `t`, entre los símbolos vigentes del top 20 del mes, MAX = mayor retorno de 1 cierre (cierre_s / cierre_{s-1} − 1) de las últimas 30 velas hasta el cierre de `t`; largo los 3 con MAX más alto y corto los 3 con MAX más bajo (sólo si hay al menos 6 vigentes). Sentido: continuación (el signo de las dos fuentes a frecuencia semanal); el signo contrario (el de Yadav, intradía) NO se prueba aparte, y tampoco otras ventanas. Entrada en la apertura de la vela siguiente. Stop a 2 ATR(14) desde la entrada y trailing a 2 ATR desde el mejor precio desde la entrada (lo mueve el motor); sin objetivo; tope 7 velas diarias. Costos: 0.1% por lado (0.05% comisión + 0.05% deslizamiento) y funding de futuros; con stop de 2 ATR diario (~5–7%) la comisión pesa ~0.03–0.04R por operación.
Es una ETAPA 1 (cribado, `reglas-de-medicion.md` § Cribado): mide sólo desarrollo, con el criterio de desarrollo completo y sin mirar nunca el holdout. Si pasa todo, queda NO_CONCLUYENTE por «holdout no mirado» y se pre-registra la etapa 2 con la misma regla y los mismos parámetros.
Riesgos declarados: (1) evidencia C+: los estudios usan monedas chicas y frecuencia semanal sin costos, y uno halla el signo contrario; el universo top 20 son las más líquidas, donde el efecto lotería debería ser más débil; (2) el MAX de 30 días cambia despacio, así que la señal persiste y las entradas se repiten en los mismos símbolos tras cada salida (el cupo de 3 por dirección y el tope de 7 días acotan la exposición; las muestras se solapan y el IC de ±2 EE es optimista: el control nulo y los tramos son el contrapeso); (3) cercana a las ideas 17 y 19 (momentum de corte transversal): un MAX alto suele coincidir con retorno reciente alto, y la dirección neta no está neutralizada por beta; (4) el holdout se declara contaminado por la familia. Criterio exigente por defecto, sin aflojar nada.

## Criterio pre-registrado

| Criterio | Valor | |
|---|---|---|
| n ≥ 300 | 2006 | ✅ |
| avgR neto > 0 y ±2 EE fuera del cero | -0.068 [-0.100, -0.037] | ❌ |
| ajustado por 4 prueba(s) de la familia: avgR − 2.50 EE > 0 | -0.068 − 2.50×0.016 = -0.107 | ❌ |
| concluyente (muestra, modelos, tramos) | sí | ✅ |
| tramos positivos ≥ 3 | 0/4 | ❌ |
| supera el percentil 95 del control nulo | -0.068 vs p95 +0.020 | ❌ |
| alcance: duración mediana ≤ 14 días | 7.0 días | ✅ |

**Motivos:** desarrollo: falla «avgR neto > 0 y ±2 EE fuera del cero» (-0.068 [-0.100, -0.037]); desarrollo: falla «ajustado por 4 prueba(s) de la familia: avgR − 2.50 EE > 0» (-0.068 − 2.50×0.016 = -0.107); desarrollo: falla «tramos positivos ≥ 3» (0/4); desarrollo: falla «supera el percentil 95 del control nulo» (-0.068 vs p95 +0.020)

## Ficha

- **Nivel:** —
- **Pruebas en la familia `corte_transversal`:** 4 (esta incluida; 1 medidas fuera de este repo)
  - `2026-11-18-momentum-transversal-1d`: RECHAZADA, desarrollo -0.012
  - `2026-11-19-momentum-transversal-1d-ret1`: RECHAZADA, desarrollo -0.022
- **Holdout contaminado:** sí
- **Pre-registro:** commit `6755482` del 2026-11-20T06:41:51Z
- **Cupo de cartera:** máx 3 por dirección
- **Peor caída (desarrollo):** -140.49 R

## Desarrollo

Ventana 2020-04-01 → 2025-09-08 · n=2006 · avgR neto -0.068 [-0.100, -0.037] · bruto -0.060 · acierto 41% · duración mediana 7.0 días

Control nulo: media -0.041, p95 +0.020

**Robustez** (informativa, no decide): costos ×1.5 → -0.076 [-0.107, -0.044] · sin las 10 mejores → -0.088 [-0.117, -0.059]

| Tramo | n | avgR neto |
|---|---|---|
| 2020-04-02 → 2021-07-21 | 502 | -0.070 |
| 2021-07-21 → 2022-12-16 | 502 | -0.048 |
| 2022-12-17 → 2024-04-27 | 501 | -0.078 |
| 2024-04-27 → 2025-09-06 | 501 | -0.077 |

| Símbolo | n | avgR neto | ±2 EE |
|---|---|---|---|
| 1000BONKUSDT | 3 | +0.008 | [-0.599, +0.616] |
| 1000FLOKIUSDT | 4 | -0.284 | [-0.815, +0.247] |
| 1000PEPEUSDT | 35 | -0.077 | [-0.341, +0.186] |
| 1000RATSUSDT | 4 | -0.149 | [-0.844, +0.545] |
| 1000SATSUSDT | 9 | +0.052 | [-0.476, +0.581] |
| 1000SHIBUSDT | 48 | -0.137 | [-0.297, +0.022] |
| 1MBABYDOGEUSDT | 1 | -0.376 | — |
| AAVEUSDT | 1 | +0.710 | — |
| ADAUSDT | 64 | +0.013 | [-0.179, +0.206] |
| ALGOUSDT | 4 | -0.185 | [-0.824, +0.453] |
| ALICEUSDT | 8 | +0.022 | [-0.302, +0.346] |
| ALPACAUSDT | 5 | -0.065 | [-0.109, -0.020] |
| APEUSDT | 12 | -0.365 | [-0.555, -0.174] |
| APTUSDT | 4 | -0.236 | [-0.689, +0.217] |
| ARBUSDT | 9 | +0.450 | [+0.062, +0.839] |
| ARKUSDT | 3 | +0.228 | [-0.196, +0.652] |
| ARPAUSDT | 3 | +0.094 | [-0.239, +0.426] |
| ATOMUSDT | 25 | -0.068 | [-0.344, +0.209] |
| AUCTIONUSDT | 1 | +0.066 | — |
| AVAXUSDT | 16 | -0.198 | [-0.484, +0.089] |
| AXSUSDT | 26 | +0.084 | [-0.167, +0.336] |
| BAKEUSDT | 3 | -0.246 | [-0.687, +0.196] |
| BANDUSDT | 9 | -0.068 | [-0.380, +0.245] |
| BATUSDT | 4 | -0.233 | [-0.882, +0.417] |
| BCHUSDT | 45 | -0.108 | [-0.313, +0.097] |
| BELUSDT | 5 | -0.383 | [-0.780, +0.014] |
| BIGTIMEUSDT | 4 | -0.241 | [-0.674, +0.192] |
| BIOUSDT | 1 | +0.360 | — |
| BLURUSDT | 3 | -0.420 | [-0.883, +0.044] |
| BLZUSDT | 8 | +0.405 | [-0.254, +1.065] |
| BNBUSDT | 222 | -0.118 | [-0.213, -0.023] |
| BNTUSDT | 1 | +1.751 | — |
| BNXUSDT | 7 | +0.183 | [-0.354, +0.720] |
| BOMEUSDT | 3 | -0.593 | [-1.268, +0.082] |
| BTCUSDT | 217 | -0.102 | [-0.197, -0.006] |
| CFXUSDT | 2 | -0.580 | [-1.311, +0.152] |
| CHRUSDT | 2 | -0.609 | [-1.277, +0.060] |
| CHZUSDT | 12 | -0.262 | [-0.649, +0.125] |
| CKBUSDT | 4 | -0.281 | [-1.140, +0.578] |
| CRVUSDT | 4 | -0.196 | [-0.596, +0.204] |
| CTSIUSDT | 5 | -0.149 | [-0.475, +0.177] |
| DASHUSDT | 1 | +0.066 | — |
| DOGEUSDT | 64 | -0.140 | [-0.297, +0.018] |
| DOTUSDT | 24 | +0.014 | [-0.269, +0.296] |
| DYDXUSDT | 9 | +0.491 | [-0.738, +1.720] |
| ENAUSDT | 12 | -0.062 | [-0.427, +0.303] |
| EOSUSDT | 36 | -0.130 | [-0.372, +0.112] |
| ETCUSDT | 49 | -0.079 | [-0.241, +0.083] |
| ETHFIUSDT | 3 | -0.403 | [-0.857, +0.051] |
| ETHUSDT | 109 | -0.049 | [-0.193, +0.094] |
| FARTCOINUSDT | 13 | +0.130 | [-0.321, +0.580] |
| FILUSDT | 23 | +0.269 | [-0.297, +0.835] |
| FLMUSDT | 3 | -0.223 | [-0.621, +0.174] |
| FRONTUSDT | 1 | -0.604 | — |
| FTMUSDT | 10 | +0.029 | [-0.214, +0.272] |
| FTTUSDT | 4 | -0.002 | [-0.006, +0.003] |
| FUNUSDT | 6 | +0.430 | [-0.988, +1.848] |
| GALAUSDT | 18 | -0.141 | [-0.361, +0.079] |
| GMTUSDT | 10 | -0.047 | [-0.461, +0.367] |
| GRTUSDT | 2 | +0.042 | [-0.835, +0.920] |
| HIGHUSDT | 1 | +1.032 | — |
| HNTUSDT | 3 | -0.364 | [-0.688, -0.039] |
| HYPERUSDT | 3 | -0.319 | [-0.540, -0.099] |
| INJUSDT | 4 | +0.035 | [-0.654, +0.725] |
| IOSTUSDT | 9 | -0.173 | [-0.586, +0.240] |
| IOTXUSDT | 1 | -0.018 | — |
| JUPUSDT | 4 | -0.457 | [-1.151, +0.237] |
| KAITOUSDT | 1 | -0.550 | — |
| KLAYUSDT | 2 | -0.413 | [-0.913, +0.087] |
| KNCUSDT | 4 | -0.261 | [-0.647, +0.126] |
| KSMUSDT | 4 | -0.002 | [-0.676, +0.672] |
| LDOUSDT | 2 | +0.082 | [-0.114, +0.277] |
| LINAUSDT | 7 | -0.027 | [-0.386, +0.331] |
| LINKUSDT | 40 | -0.117 | [-0.345, +0.111] |
| LITUSDT | 3 | -0.536 | [-0.976, -0.095] |
| LPTUSDT | 3 | +0.044 | [-0.711, +0.798] |
| LQTYUSDT | 1 | -0.071 | — |
| LTCUSDT | 59 | -0.000 | [-0.162, +0.161] |
| LUNAUSDT | 6 | +0.134 | [-0.555, +0.823] |
| MANAUSDT | 6 | +0.214 | [-0.172, +0.600] |
| MASKUSDT | 7 | -0.173 | [-0.569, +0.223] |
| MATICUSDT | 22 | +0.031 | [-0.238, +0.301] |
| MKRUSDT | 2 | -0.085 | [-1.895, +1.726] |
| MOODENGUSDT | 4 | +0.036 | [-0.765, +0.836] |
| MTLUSDT | 2 | -0.136 | [-1.545, +1.273] |
| NEARUSDT | 11 | -0.113 | [-0.408, +0.183] |
| NEIROUSDT | 2 | -0.207 | [-0.390, -0.024] |
| NEOUSDT | 13 | -0.075 | [-0.412, +0.262] |
| NOTUSDT | 7 | -0.451 | [-0.724, -0.179] |
| OMGUSDT | 4 | -0.201 | [-0.570, +0.168] |
| ONGUSDT | 1 | -0.328 | — |
| ONTUSDT | 1 | +0.196 | — |
| OPUSDT | 12 | -0.229 | [-0.442, -0.017] |
| ORDIUSDT | 7 | +0.096 | [-0.449, +0.641] |
| PENGUUSDT | 3 | -0.303 | [-0.871, +0.265] |
| PEOPLEUSDT | 10 | -0.097 | [-0.421, +0.226] |
| PNUTUSDT | 7 | +0.180 | [-0.231, +0.592] |
| RAREUSDT | 4 | -0.026 | [-0.268, +0.217] |
| REEFUSDT | 7 | +0.222 | [-0.378, +0.821] |
| RNDRUSDT | 3 | +0.031 | [-0.458, +0.520] |
| RUNEUSDT | 4 | -0.493 | [-0.803, -0.182] |
| RVNUSDT | 3 | -0.308 | [-0.755, +0.139] |
| SANDUSDT | 18 | -0.163 | [-0.368, +0.041] |
| SEIUSDT | 6 | -0.427 | [-0.789, -0.065] |
| SOLUSDT | 25 | -0.108 | [-0.394, +0.178] |
| STMXUSDT | 7 | -0.247 | [-0.559, +0.065] |
| STORJUSDT | 10 | -0.069 | [-0.421, +0.283] |
| STXUSDT | 1 | +0.181 | — |
| SUIUSDT | 12 | +0.220 | [-0.527, +0.968] |
| SUSHIUSDT | 6 | -0.019 | [-0.713, +0.676] |
| SXPUSDT | 8 | -0.199 | [-0.456, +0.057] |
| THETAUSDT | 7 | -0.075 | [-0.576, +0.425] |
| TIAUSDT | 8 | +0.003 | [-0.358, +0.363] |
| TOMOUSDT | 3 | +0.027 | [-0.017, +0.071] |
| TRBUSDT | 14 | +0.199 | [-0.275, +0.674] |
| TRUMPUSDT | 10 | -0.310 | [-0.598, -0.022] |
| TRXUSDT | 29 | -0.065 | [-0.322, +0.192] |
| TURBOUSDT | 1 | -0.001 | — |
| UMAUSDT | 2 | -0.266 | [-1.522, +0.989] |
| UNFIUSDT | 8 | +0.248 | [-0.477, +0.973] |
| UNIUSDT | 13 | +0.093 | [-0.381, +0.567] |
| UXLINKUSDT | 3 | -0.344 | [-0.700, +0.012] |
| VETUSDT | 7 | +0.448 | [-0.288, +1.183] |
| VIRTUALUSDT | 2 | +0.151 | [-0.071, +0.374] |
| VOXELUSDT | 4 | -0.398 | [-0.820, +0.024] |
| WAVESUSDT | 15 | -0.005 | [-0.315, +0.305] |
| WIFUSDT | 16 | +0.030 | [-0.277, +0.338] |
| WLDUSDT | 16 | -0.158 | [-0.474, +0.158] |
| XLMUSDT | 27 | +0.112 | [-0.317, +0.541] |
| XMRUSDT | 5 | -0.096 | [-0.414, +0.221] |
| XRPUSDT | 156 | -0.094 | [-0.210, +0.021] |
| XTZUSDT | 1 | -0.266 | — |
| YFIUSDT | 6 | +0.234 | [-0.375, +0.842] |
| ZECUSDT | 10 | -0.150 | [-0.506, +0.205] |
| ZILUSDT | 7 | -0.203 | [-0.602, +0.197] |
| ZRXUSDT | 1 | -0.115 | — |

53 símbolos del universo sin operaciones en este tramo.

## Holdout

No se miró: desarrollo no pasó el criterio.
