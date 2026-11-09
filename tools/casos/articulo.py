"""Lectura de los artículos derivados de medsemiotics-db (``posts/*.md``).

Solo se lee: los artículos pertenecen a ``generate_topic.py`` y se regeneran desde la base.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import yaml

from casos.errores import ErrorDeCaso

if TYPE_CHECKING:
    from pathlib import Path

ENCABEZADO_HALLAZGO = re.compile(r"^### (?P<nombre>.+) \((?P<id>HM:\d+)\)$", re.M)
REFERENCIA = re.compile(r"^\*\*(?P<id>pmid:\d+):\*\* (?P<cita>.+)$", re.M)


@dataclass(frozen=True)
class Articulo:
    """Lo que un caso puede citar de un artículo: su evidencia, con nombres y referencias."""

    ruta: Path
    condicion_id: str
    condicion_nombre: str
    slug: str
    fecha: str
    revision_fuente: str
    concepto_principal: str | None
    evidencia: dict[str, list[dict[str, Any]]]
    nombres: dict[str, str]
    referencias: dict[str, str]


def _dividir(texto: str, ruta: Path) -> tuple[dict[str, Any], str]:
    partes = re.split(r"^---\s*$", texto, maxsplit=2, flags=re.M)
    if len(partes) != 3:
        raise ErrorDeCaso(f"{ruta.name}: artículo sin frontmatter YAML.")
    datos = yaml.safe_load(partes[1])
    if not isinstance(datos, dict):
        raise ErrorDeCaso(f"{ruta.name}: frontmatter no es un mapa.")
    return datos, partes[2]


def leer_articulo(ruta: Path) -> Articulo:
    datos, cuerpo = _dividir(ruta.read_text(encoding="utf-8"), ruta)
    grounding = datos.get("grounding") or {}
    fuente = datos.get("fuente") or {}
    condicion_id = grounding.get("condicion_id")
    if not isinstance(condicion_id, str) or not fuente.get("revision"):
        raise ErrorDeCaso(f"{ruta.name}: artículo sin procedencia de medsemiotics-db.")
    # Un mismo hallazgo puede medirse en varias poblaciones: se conservan todas.
    evidencia: dict[str, list[dict[str, Any]]] = {}
    for item in datos.get("evidencia") or []:
        concepto = item.get("concepto")
        if not isinstance(concepto, str):
            raise ErrorDeCaso(f"{ruta.name}: evidencia sin concepto.")
        evidencia.setdefault(concepto, []).append(item)
    nombres = {m["id"]: m["nombre"] for m in ENCABEZADO_HALLAZGO.finditer(cuerpo)}
    sin_nombre = sorted(set(evidencia) - set(nombres))
    if sin_nombre:
        raise ErrorDeCaso(f"{ruta.name}: hallazgos sin nombre en el cuerpo: {sin_nombre}")
    return Articulo(
        ruta=ruta,
        condicion_id=condicion_id,
        condicion_nombre=str(grounding.get("condicion_nombre") or condicion_id),
        slug=str(datos["slug"]),
        fecha=str(datos["date"]),
        revision_fuente=str(fuente["revision"]),
        concepto_principal=grounding.get("concepto_id"),
        evidencia=evidencia,
        nombres=nombres,
        referencias={m["id"]: m["cita"].strip() for m in REFERENCIA.finditer(cuerpo)},
    )


def leer_articulos(directorio: Path) -> dict[str, Articulo]:
    """Artículos por ID de condición (``HM:6003``)."""
    resultado: dict[str, Articulo] = {}
    for ruta in sorted(directorio.glob("*.md")):
        articulo = leer_articulo(ruta)
        if articulo.condicion_id in resultado:
            raise ErrorDeCaso(f"Condición duplicada en posts/: {articulo.condicion_id}")
        resultado[articulo.condicion_id] = articulo
    return resultado
