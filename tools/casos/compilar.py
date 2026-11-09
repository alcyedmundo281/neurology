"""Validación cruzada caso ↔ artículo y compilación a ``assets/data/casos/<slug>.json``.

Solo los casos ``publicado`` generan JSON; los borradores se validan igual, pero no llegan
al sitio. ``build-blog.mjs`` incorpora el JSON compilado al artículo correspondiente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import ValidationError

from casos.articulo import Articulo, leer_articulos
from casos.errores import ErrorDeCaso
from casos.evidencia import referencias_de, resolver, resumen
from casos.modelo import ETIQUETA_FASE, Caso, Dato

if TYPE_CHECKING:
    from datetime import date

RAIZ = Path(__file__).resolve().parents[2]
AVISO = (
    "Caso clínico ficticio con fines docentes. Las cifras de evidencia provienen de "
    "medsemiotics-db y se actualizan con la base; el relato clínico no describe a un "
    "paciente real."
)


@dataclass(frozen=True)
class Rutas:
    raiz: Path

    @property
    def casos(self) -> Path:
        return self.raiz / "casos"

    @property
    def posts(self) -> Path:
        return self.raiz / "posts"

    @property
    def salida(self) -> Path:
        return self.raiz / "assets" / "data" / "casos"


@dataclass(frozen=True)
class CasoLeido:
    ruta: Path
    caso: Caso
    articulo: Articulo


def nombre_archivo(condicion_id: str) -> str:
    return condicion_id.replace(":", "") + ".yaml"


def cargar_caso(ruta: Path) -> Caso:
    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        return Caso.model_validate(datos)
    except yaml.YAMLError as error:
        raise ErrorDeCaso(f"{ruta.name}: YAML inválido: {error}") from error
    except ValidationError as error:
        detalle = "\n".join(
            f"  {'.'.join(str(p) for p in e['loc']) or '(caso)'}: {e['msg']}"
            for e in error.errors()
        )
        raise ErrorDeCaso(f"{ruta.name}: no cumple el esquema:\n{detalle}") from error


def leer_casos(rutas: Rutas) -> list[CasoLeido]:
    articulos = leer_articulos(rutas.posts)
    leidos: list[CasoLeido] = []
    errores: list[str] = []
    for ruta in sorted(rutas.casos.glob("*.yaml")) if rutas.casos.is_dir() else []:
        try:
            caso = cargar_caso(ruta)
            if ruta.name != nombre_archivo(caso.condicion_id):
                raise ErrorDeCaso(
                    f"{ruta.name}: debe llamarse {nombre_archivo(caso.condicion_id)}."
                )
            articulo = articulos.get(caso.condicion_id)
            if articulo is None:
                raise ErrorDeCaso(f"{ruta.name}: no hay artículo para {caso.condicion_id}.")
            leidos.append(CasoLeido(ruta, caso, articulo))
        except ErrorDeCaso as error:
            errores.append(str(error))
    if errores:
        raise ErrorDeCaso("\n".join(errores))
    return leidos


def _cobertura(caso: Caso, articulo: Articulo, donde: str) -> None:
    """La base es el eje: ningún hallazgo registrado desaparece del caso sin un motivo."""
    evidencia = set(articulo.evidencia)
    revelados = [h for etapa in caso.etapas for h in etapa.hallazgos]
    omitidos = [o.hallazgo for o in caso.omitidos]
    errores: list[str] = []
    for concepto in sorted(set(revelados + omitidos) - evidencia):
        errores.append(f"{concepto} no está en la evidencia de {articulo.condicion_id}.")
    for concepto in sorted({c for c in revelados if revelados.count(c) > 1}):
        errores.append(f"{concepto} se revela en más de una etapa.")
    for concepto in sorted(set(revelados) & set(omitidos)):
        errores.append(f"{concepto} está revelado y a la vez omitido.")
    faltan = sorted(evidencia - set(revelados) - set(omitidos))
    if faltan:
        nombres = ", ".join(f"{c} ({articulo.nombres[c]})" for c in faltan)
        errores.append(f"hallazgos de la base sin etapa ni motivo de omisión: {nombres}")
    principal = articulo.concepto_principal
    if principal and principal not in revelados:
        errores.append(
            f"el hallazgo principal del artículo, {principal} ({articulo.nombres[principal]}), "
            "debe revelarse en una etapa."
        )
    if errores:
        raise ErrorDeCaso(f"{donde}:\n" + "\n".join("  " + e for e in errores))


def _datos(datos: list[Dato], articulo: Articulo, donde: str) -> list[dict[str, str]]:
    return [
        {
            "etiqueta": resolver(d.etiqueta, articulo, (), f"{donde}.datos[{i}]"),
            "valor": resolver(d.valor, articulo, (), f"{donde}.datos[{i}]"),
        }
        for i, d in enumerate(datos)
    ]


def compilar(leido: CasoLeido, hoy: date) -> dict[str, Any]:
    caso, articulo = leido.caso, leido.articulo
    donde = leido.ruta.name
    fecha = caso.publicacion.fecha
    if fecha is not None and fecha > hoy:
        raise ErrorDeCaso(f"{donde}: la fecha de publicación {fecha} es futura.")
    if caso.publicacion.revisiones and caso.publicacion.revisiones[-1].fecha > hoy:
        raise ErrorDeCaso(f"{donde}: hay una revisión con fecha futura.")
    _cobertura(caso, articulo, donde)

    # La viñeta y los objetivos no citan evidencia: el estudiante aún no la tiene.
    def texto(valor: str, permitidos: set[str], lugar: str) -> str:
        return resolver(valor, articulo, permitidos, f"{donde}: {lugar}")

    revelados: set[str] = set()
    etapas: list[dict[str, Any]] = []
    for numero, etapa in enumerate(caso.etapas, 1):
        lugar = f"etapa {numero}"
        revelados |= set(etapa.hallazgos)
        etapas.append(
            {
                "numero": numero,
                "titulo": texto(etapa.titulo, set(), lugar),
                "fase": etapa.fase,
                "fase_etiqueta": ETIQUETA_FASE[etapa.fase],
                "informacion": texto(etapa.informacion, revelados, lugar)
                if etapa.informacion
                else None,
                "datos": _datos(etapa.datos, articulo, f"{donde}: {lugar}"),
                "hallazgos": [f for c in etapa.hallazgos for f in resumen(c, articulo)],
                "preguntas": [
                    {
                        "pregunta": texto(p.pregunta, revelados, f"{lugar}, pregunta {i}"),
                        "clave": texto(p.clave, revelados, f"{lugar}, clave {i}"),
                    }
                    for i, p in enumerate(etapa.preguntas, 1)
                ],
            }
        )
    citadas = sorted(
        {r for c in revelados for r in referencias_de(articulo.evidencia[c])},
        key=lambda r: (not r.startswith("pmid:"), r),
    )
    sin_cita = [r for r in citadas if r not in articulo.referencias]
    if sin_cita:
        raise ErrorDeCaso(f"{donde}: referencias sin cita en el artículo: {sin_cita}")
    return {
        "condicion_id": caso.condicion_id,
        "slug": articulo.slug,
        "estado": caso.estado,
        "autoria": caso.autoria.model_dump(),
        "publicacion": {
            "fecha": fecha.isoformat() if fecha else None,
            "version": caso.publicacion.version,
            "ultima_revision": (
                caso.publicacion.ultima_fecha.isoformat() if caso.publicacion.ultima_fecha else None
            ),
            "revisiones": [
                {"fecha": r.fecha.isoformat(), "nota": r.nota} for r in caso.publicacion.revisiones
            ],
        },
        "fuente_revision": articulo.revision_fuente,
        "nivel": caso.nivel,
        "duracion_min": caso.duracion_min,
        "aviso": AVISO,
        "objetivos": [texto(o, set(), f"objetivo {i}") for i, o in enumerate(caso.objetivos, 1)],
        "vineta": {
            "titulo": texto(caso.vineta.titulo, set(), "viñeta"),
            "texto": texto(caso.vineta.texto, set(), "viñeta"),
            "datos": _datos(caso.vineta.datos, articulo, f"{donde}: viñeta"),
        },
        "etapas": etapas,
        "cierre": {
            "sintesis": texto(caso.cierre.sintesis, revelados, "cierre"),
            "necesidades_aprendizaje": [
                texto(n, revelados, "cierre") for n in caso.cierre.necesidades_aprendizaje
            ],
        },
        "omitidos": [
            {
                "id": o.hallazgo,
                "nombre": articulo.nombres[o.hallazgo],
                "motivo": texto(o.motivo, set(), "omitidos"),
            }
            for o in caso.omitidos
        ],
        "referencias": [{"id": r, "cita": articulo.referencias[r]} for r in citadas],
    }


def serializar(datos: dict[str, Any]) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def construir(rutas: Rutas, hoy: date, *, solo_comprobar: bool) -> list[str]:
    """Valida todos los casos y escribe (o compara) el JSON de los publicados.

    Devuelve las rutas desactualizadas en modo comprobación, o las escritas en modo build.
    """
    leidos = leer_casos(rutas)
    esperados: dict[Path, str] = {}
    errores: list[str] = []
    for leido in leidos:
        try:
            datos = compilar(leido, hoy)
        except ErrorDeCaso as error:
            errores.append(str(error))
            continue
        if leido.caso.estado == "publicado":
            esperados[rutas.salida / f"{leido.articulo.slug}.json"] = serializar(datos)
    if errores:
        raise ErrorDeCaso("\n".join(errores))
    existentes = set(rutas.salida.glob("*.json")) if rutas.salida.is_dir() else set()
    cambios = [
        ruta
        for ruta, contenido in esperados.items()
        if not ruta.exists() or ruta.read_text(encoding="utf-8") != contenido
    ]
    sobrantes = sorted(existentes - set(esperados))
    if not solo_comprobar:
        rutas.salida.mkdir(parents=True, exist_ok=True)
        for ruta in cambios:
            ruta.write_text(esperados[ruta], encoding="utf-8", newline="\n")
        for ruta in sobrantes:
            ruta.unlink()
    return [_relativa(r, rutas.raiz) for r in sorted(cambios) + sobrantes]


def _relativa(ruta: Path, raiz: Path) -> str:
    return ruta.relative_to(raiz).as_posix()


def esqueleto(articulo: Articulo, autor: dict[str, Any]) -> str:
    """Borrador inicial con todos los hallazgos de la base listados para asignarlos a etapas."""
    lineas = [
        f"# Caso socrático para {articulo.condicion_nombre} ({articulo.condicion_id}).",
        "# Asigne cada hallazgo a una etapa o justifique su omisión en «omitidos».",
        "# Hallazgos registrados en medsemiotics-db:",
    ]
    for concepto, items in articulo.evidencia.items():
        marca = " ← principal" if concepto == articulo.concepto_principal else ""
        varias = f", {len(items)} poblaciones: use @1..@{len(items)}" if len(items) > 1 else ""
        lineas.append(
            f"#   {concepto}  {articulo.nombres[concepto]} "
            f"[{items[0].get('rol')}, {items[0].get('estado_lr')}{varias}]{marca}"
        )
    principal = articulo.concepto_principal or next(iter(articulo.evidencia), "HM:0000")
    plantilla = {
        "condicion_id": articulo.condicion_id,
        "estado": "borrador",
        "autoria": {"autores": [autor], "revisor": None},
        "nivel": "Pregrado",
        "duracion_min": 45,
        "objetivos": ["PENDIENTE"],
        "vineta": {"titulo": "PENDIENTE", "texto": "PENDIENTE: relato clínico ficticio."},
        "etapas": [
            {
                "titulo": "Hipótesis iniciales",
                "fase": "activacion",
                "preguntas": [{"pregunta": "PENDIENTE pregunta", "clave": "PENDIENTE clave"}],
            },
            {
                "titulo": "Exploración",
                "fase": "exploracion",
                "hallazgos": [principal],
                "preguntas": [{"pregunta": "PENDIENTE pregunta", "clave": "PENDIENTE clave"}],
            },
            {
                "titulo": "Discriminación",
                "fase": "discriminacion",
                "hallazgos": [],
                "preguntas": [{"pregunta": "PENDIENTE pregunta", "clave": "PENDIENTE clave"}],
            },
            {
                "titulo": "Decisión",
                "fase": "decision",
                "preguntas": [{"pregunta": "PENDIENTE pregunta", "clave": "PENDIENTE clave"}],
            },
        ],
        "cierre": {"sintesis": "PENDIENTE síntesis", "necesidades_aprendizaje": ["PENDIENTE"]},
        "omitidos": [],
    }
    cuerpo = yaml.safe_dump(plantilla, allow_unicode=True, sort_keys=False, width=100)
    return "\n".join(lineas) + "\n" + cuerpo
