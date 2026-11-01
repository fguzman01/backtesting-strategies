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
CRITERIOS = {"n_minimo", "ic95_excluye_cero", "concluyente", "tramos_positivos_minimo", "supera_nulo_p95"}


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
    )
    if desde is not None:
        pd.Timestamp(desde)  # que sea una fecha
    return Spec(sid, estado, hipotesis, tipo, modulo, params, mercado, simbolos, intervalo, funding, cfg,
                str(desde) if desde else None, criterio, ruta, d, historia_spot)


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
