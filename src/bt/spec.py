"""Pre-registros (`specs/*.yaml`): carga y validación.

Una spec se escribe ANTES de correr nada. Fija la hipótesis, las reglas, el universo, la ventana y
el criterio de aprobación. La validación aplica también el alcance de 02-DOCS/alcance.md: señal
entre 5m y 1d y un timeout de como mucho 14 días.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from bt.engine import Config

INTERVALOS = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480,
              "12h": 720, "1d": 1440}
TIMEOUT_MAX_DIAS = 14
DURACION_MEDIANA_MAX_DIAS = 7
TIPOS = {"scalp", "swing", "diario"}
ESTADOS = {"borrador", "pre-registrada", "referencia"}
CRITERIOS = {"n_minimo", "ic95_excluye_cero", "concluyente", "tramos_positivos_minimo", "supera_nulo_p95",
             "estabilidad_minima", "ajuste_por_pruebas"}


# Familia de los módulos anteriores a que existiera `familia` en la spec (2026-11-02): sin esto, las
# variantes viejas no cuentan en n_pruebas de una spec nueva de la misma familia.
FAMILIA_POR_MODULO = {
    "tendencia_donchian": "tendencia", "tendencia_chandelier": "tendencia", "tendencia_trailing": "tendencia",
    "donchian_breakout": "tendencia", "reversion_salto": "reversion",
}


class SpecInvalida(ValueError):
    pass


@dataclass(frozen=True)
class Criterio:
    n_minimo: int = 30
    ic95_excluye_cero: bool = True
    concluyente: bool = True
    tramos_positivos_minimo: int = 0
    supera_nulo_p95: bool = True
    holdout_avg_positivo: bool = True
    # Endurecido el 2026-11-02 (Felipe), tras 2026-11-02-trend4h-tope-7d: su holdout dio +0.036 con el
    # intervalo en el cero y negativo sin sus 10 mejores, y aun así pasaba «avgR > 0». Por defecto
    # estrictos; las evaluaciones ya hechas no se re-evalúan, así que no cambian.
    holdout_aguanta_costos: bool = True  # con costos ×1.5 el avgR del holdout sigue > 0
    holdout_sin_mejores_no_negativo: bool = True  # sin las 10 mejores operaciones, avgR ≥ 0
    holdout_fraccion_desarrollo: float = 0.33  # el avgR del holdout conserva al menos 1/3 del de desarrollo
    # Estabilidad de parámetros (2026-11-03): con todos los parámetros numéricos ×0.8 y ×1.2, el avgR de
    # desarrollo conserva al menos esta fracción del original. None = se mide igual, pero sólo informa.
    estabilidad_minima: float | None = None
    # Corrección por número de pruebas (2026-11-04, B-02): el margen sobre el cero crece con las
    # variantes probadas de la familia (Bonferroni). False en specs viejas que no lo declaran.
    ajuste_por_pruebas: bool = False


@dataclass(frozen=True)
class Spec:
    id: str
    estado: str
    hipotesis: str
    tipo: str
    modulo: str
    params: dict
    mercado: str
    simbolos: list[str]
    intervalo: str
    funding: bool
    cfg: Config
    desde: str | None
    criterio: Criterio
    ruta: Path | None = None
    crudo: dict = field(default_factory=dict, repr=False)
    historia_spot: bool = False
    # Retroalimentación de btc-signal-web sobre la primera aprobada (2026-11-02):
    familia: str = ""  # para contar cuántas variantes se probaron (n_pruebas)
    holdout_contaminado: bool = False  # el período ya se miró con algo emparentado (p. ej. btc-signal-web)
    madre: dict | None = None  # estrategia de la que es variante: se corre al lado en el mismo período y tokens
    medicion: bool = False  # pregunta de medición, no estrategia para operar: nunca va a approved.json
    solo_desarrollo: bool = False  # medición que nunca mira el holdout (ni de la hija, ni de la madre)
    pruebas_previas: int = 0  # variantes de la familia medidas FUERA de este repo (p. ej. btc-signal-web)
    dinamico_top: int | None = None  # universo dinámico: los `top` de cada mes (bt.universo)
    miembros: dict | None = field(default=None, repr=False)  # {símbolo: meses AAAA-MM}, lo resuelve evaluar
    max_por_direccion: int | None = None  # cupo de cartera como en el bot (posiciones abiertas por dirección)

    @property
    def minutos_por_vela(self) -> int:
        return INTERVALOS[self.intervalo]


def _exigir(d: dict, clave: str, donde: str):
    if clave not in d or d[clave] in (None, ""):
        raise SpecInvalida(f"falta `{donde}{clave}`")
    return d[clave]


def desde_dict(d: dict, ruta: Path | None = None) -> Spec:
    if not isinstance(d, dict):
        raise SpecInvalida("la spec tiene que ser un diccionario YAML")
    sid = str(_exigir(d, "id", ""))
    if ruta is not None and ruta.stem != sid:
        raise SpecInvalida(f"el id `{sid}` no coincide con el nombre del archivo `{ruta.name}`")
    estado = _exigir(d, "estado", "")
    if estado not in ESTADOS:
        raise SpecInvalida(f"estado `{estado}` inválido; usar uno de {sorted(ESTADOS)}")
    hipotesis = str(_exigir(d, "hipotesis", "")).strip()

    hz = _exigir(d, "horizonte", "")
    tipo = _exigir(hz, "tipo", "horizonte.")
    if tipo not in TIPOS:
        raise SpecInvalida(f"horizonte.tipo `{tipo}` inválido; usar uno de {sorted(TIPOS)}")

    est = _exigir(d, "estrategia", "")
    modulo = str(_exigir(est, "modulo", "estrategia."))
    if not modulo.isidentifier():
        raise SpecInvalida(f"estrategia.modulo `{modulo}` no es un nombre de módulo válido")
    params = est.get("params") or {}

    uni = _exigir(d, "universo", "")
    mercado = uni.get("mercado", "futures")
    if mercado not in ("futures", "spot"):
        raise SpecInvalida(f"universo.mercado `{mercado}` inválido")
    dinamico = uni.get("dinamico")
    top = None
    if dinamico is not None:
        # Universo sin sesgo de supervivencia (bt.universo): los `top` más operados de cada mes.
        top = dinamico.get("top") if isinstance(dinamico, dict) else None
        if not isinstance(top, int) or not 1 <= top <= 50:
            raise SpecInvalida("universo.dinamico.top tiene que ser un entero entre 1 y 50")
        if mercado != "futures":
            raise SpecInvalida("universo.dinamico sólo existe para futuros USDT")
        if uni.get("historia_spot"):
            raise SpecInvalida("universo.dinamico no se combina con historia_spot (la tabla empieza en 2019-12)")
        simbolos = []
    else:
        simbolos = [str(s).upper() for s in _exigir(uni, "simbolos", "universo.")]
    intervalo = str(_exigir(uni, "intervalo", "universo."))
    if intervalo not in INTERVALOS:
        raise SpecInvalida(
            f"universo.intervalo `{intervalo}` fuera del alcance (02-DOCS/alcance.md): usar uno de "
            f"{list(INTERVALOS)}"
        )
    funding = bool(uni.get("funding", mercado == "futures"))
    if funding and mercado != "futures":
        raise SpecInvalida("el funding sólo existe en futuros")
    historia_spot = bool(uni.get("historia_spot", False))
    if historia_spot and mercado != "futures":
        raise SpecInvalida("historia_spot completa con spot la historia de los FUTUROS; con mercado spot no aplica")

    c = d.get("config") or {}
    timeout = c.get("timeout_velas")
    if not timeout:
        raise SpecInvalida(f"falta `config.timeout_velas` (obligatorio, como mucho {TIMEOUT_MAX_DIAS} días)")
    dias = int(timeout) * INTERVALOS[intervalo] / 1440
    if dias > TIMEOUT_MAX_DIAS:
        raise SpecInvalida(
            f"config.timeout_velas={timeout} en {intervalo} son {dias:g} días; el alcance permite "
            f"{TIMEOUT_MAX_DIAS} como máximo"
        )
    cfg = Config(
        fee_pct_por_lado=float(c.get("fee_pct_por_lado", 0.0005)),
        deslizamiento_pct=float(c.get("deslizamiento_pct", 0.0)),
        timeout_velas=int(timeout),
        objetivo_r=c.get("objetivo_r"),
        cerrar_al_final=bool(c.get("cerrar_al_final", True)),
        breakeven_r=float(c["breakeven_r"]) if c.get("breakeven_r") is not None else None,
        tp1_r=float(c["tp1_r"]) if c.get("tp1_r") is not None else None,
        tp1_cierre=float(c.get("tp1_cierre", 1.0)),
    )
    if not 0 < cfg.tp1_cierre <= 1:
        raise SpecInvalida("config.tp1_cierre tiene que estar entre 0 (excluido) y 1")
    if cfg.fee_pct_por_lado <= 0:
        raise SpecInvalida("config.fee_pct_por_lado tiene que ser positivo: sin comisión no hay resultado")

    vd = d.get("ventana_desarrollo") or {}
    desde = vd.get("desde")

    cr = _exigir(d, "criterio_aprobacion", "")
    desconocidos = set(cr) - CRITERIOS - {"holdout"}
    if desconocidos:
        raise SpecInvalida(f"criterios desconocidos: {sorted(desconocidos)}")
    ho = cr.get("holdout") or {}
    criterio = Criterio(
        n_minimo=int(_exigir(cr, "n_minimo", "criterio_aprobacion.")),
        ic95_excluye_cero=bool(cr.get("ic95_excluye_cero", True)),
        concluyente=bool(cr.get("concluyente", True)),
        tramos_positivos_minimo=int(cr.get("tramos_positivos_minimo", 0)),
        supera_nulo_p95=bool(cr.get("supera_nulo_p95", True)),
        holdout_avg_positivo=bool(ho.get("avgRNeto_positivo", True)),
        holdout_aguanta_costos=bool(ho.get("aguanta_costos", True)),
        holdout_sin_mejores_no_negativo=bool(ho.get("sin_mejores_no_negativo", True)),
        holdout_fraccion_desarrollo=float(ho.get("fraccion_desarrollo_minima", 0.33)),
        estabilidad_minima=None if cr.get("estabilidad_minima") is None else float(cr["estabilidad_minima"]),
        ajuste_por_pruebas=bool(cr.get("ajuste_por_pruebas", False)),
    )
    if desde is not None:
        pd.Timestamp(desde)  # que sea una fecha
    familia = str(d.get("familia") or FAMILIA_POR_MODULO.get(modulo, modulo))
    madre = d.get("madre")
    if madre is not None:
        if not isinstance(madre, dict):
            raise SpecInvalida("`madre` tiene que ser un diccionario (modulo, params, config)")
        m_mod = str(madre.get("modulo", modulo))
        if not m_mod.isidentifier():
            raise SpecInvalida(f"madre.modulo `{m_mod}` no es un nombre de módulo válido")
        madre = {"modulo": m_mod, "params": madre.get("params", params) or {},
                 "config": madre.get("config") or {}, "nombre": str(madre.get("nombre") or m_mod)}
    previas = d.get("pruebas_previas", 0)
    if not isinstance(previas, int) or previas < 0:
        raise SpecInvalida("`pruebas_previas` tiene que ser un entero ≥ 0 (variantes medidas fuera de este repo)")
    solo_desarrollo = bool(d.get("solo_desarrollo", False))
    if solo_desarrollo and not bool(d.get("medicion", False)):
        raise SpecInvalida("`solo_desarrollo: true` sólo vale junto con `medicion: true` "
                           "(una estrategia para operar tiene que pasar por el holdout)")
    cupo = c.get("max_por_direccion")
    if cupo is not None and (not isinstance(cupo, int) or cupo < 1):
        raise SpecInvalida("config.max_por_direccion tiene que ser un entero ≥ 1 (o no ponerlo)")
    return Spec(sid, estado, hipotesis, tipo, modulo, params, mercado, simbolos, intervalo, funding, cfg,
                str(desde) if desde else None, criterio, ruta, d, historia_spot,
                familia=familia, holdout_contaminado=bool(d.get("holdout_contaminado", False)),
                madre=madre, max_por_direccion=cupo, pruebas_previas=previas, dinamico_top=top,
                medicion=bool(d.get("medicion", False)), solo_desarrollo=solo_desarrollo)


def cargar(ruta: Path | str) -> Spec:
    ruta = Path(ruta)
    try:
        d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SpecInvalida(f"{ruta}: YAML inválido: {e}") from e
    try:
        return desde_dict(d, ruta)
    except SpecInvalida as e:
        raise SpecInvalida(f"{ruta}: {e}") from e


def listar(directorio: Path = Path("specs")) -> list[Path]:
    return sorted(p for p in directorio.glob("*.yaml") if p.name != "PLANTILLA.yaml")
