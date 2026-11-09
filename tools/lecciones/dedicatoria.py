"""Dedicatoria (``lecciones/paratextos/dedicatoria.md``): página propia tras los créditos.

Como «Sobre los autores», la aprueban los autores vivos antes de imprimirse. La aprobación vive en
el frontmatter (``estado``, ``aprobada_por`` y ``fecha``) y la compilación del libro falla mientras
la dedicatoria siga en «propuesta». Las fechas de vida de la persona dedicada salen del mapa.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

from lecciones.mapa import cargar
from lecciones.semblanzas import separar

if TYPE_CHECKING:
    from pathlib import Path

    from lecciones.mapa import Mapa

RUTA = ("lecciones", "paratextos", "dedicatoria.md")
NOMBRE_ARCHIVO = "lecciones/paratextos/dedicatoria.md"
ESTADOS = ("propuesta", "aprobada")
# La persona a quien se dedica. Su nombre y sus fechas salen del mapa.
DEDICADA = "atc"
_VIDA = re.compile(r"\{vida:([a-z]+)\}")


def _vida(mapa: Mapa, clave: str) -> str | None:
    persona = mapa.personas.get(clave)
    if persona is None or persona.nacimiento is None or persona.fallecimiento is None:
        return None
    return f"{persona.nacimiento.year}–{persona.fallecimiento.year}"


def renderizar(texto: str, mapa: Mapa) -> str:
    """La dedicatoria tal como se imprime: sin frontmatter y con las fechas del mapa."""
    cuerpo = separar(texto)[1].strip()

    def fechas(m: re.Match[str]) -> str:
        return _vida(mapa, m.group(1)) or m.group(0)

    return _VIDA.sub(fechas, cuerpo) + "\n"


def problemas_de_dedicatoria(texto: str, mapa: Mapa) -> list[str]:
    """Defectos de ``dedicatoria.md``: fechas del mapa, texto y aprobación de los autores vivos."""
    datos, cuerpo = separar(texto)
    problemas: list[str] = []
    dedicada = mapa.personas.get(DEDICADA)
    if dedicada is None or _vida(mapa, DEDICADA) is None:
        problemas.append(
            f"{NOMBRE_ARCHIVO}: lecciones/mapa.yaml debe dar nacimiento y fallecimiento de "
            f"«{DEDICADA}»"
        )
    elif dedicada.nombre not in cuerpo:
        problemas.append(
            f"{NOMBRE_ARCHIVO}: el texto debe nombrar a {dedicada.nombre} como el mapa"
        )
    if not any(m.group(1) == DEDICADA for m in _VIDA.finditer(cuerpo)):
        problemas.append(f"{NOMBRE_ARCHIVO}: las fechas salen del mapa: use {{vida:{DEDICADA}}}")
    if re.search(r"\d{4}\s*[–-]\s*\d{4}", cuerpo):
        problemas.append(f"{NOMBRE_ARCHIVO}: no escriba las fechas a mano; use {{vida:{DEDICADA}}}")
    if not cuerpo.strip():
        problemas.append(f"{NOMBRE_ARCHIVO}: sin texto")

    estado = datos.get("estado")
    if estado not in ESTADOS:
        problemas.append(f"{NOMBRE_ARCHIVO}: estado debe ser {' o '.join(ESTADOS)}")
    aprobada = datos.get("aprobada_por") or []
    aprobada = {aprobada} if isinstance(aprobada, str) else set(aprobada)
    desconocidos = aprobada - set(mapa.personas)
    if desconocidos:
        problemas.append(f"{NOMBRE_ARCHIVO}: aprobada_por desconoce {sorted(desconocidos)}")
    vivos = {k for k, p in mapa.personas.items() if not p.fallecido}
    if estado != "aprobada":
        problemas.append("dedicatoria: propuesta, sin aprobar por los autores vivos")
    elif faltan := vivos - aprobada:
        quienes = ", ".join(mapa.personas[k].nombre for k in sorted(faltan))
        problemas.append(f"dedicatoria: sin aprobar por {quienes}")
    elif not isinstance(datos.get("fecha"), date):
        problemas.append("dedicatoria: falta la fecha de aprobación")
    return problemas


def verificar(raiz: Path) -> list[str]:
    """Problemas de ``dedicatoria.md`` de un repositorio (vacío: puede imprimirse)."""
    ruta = raiz.joinpath(*RUTA)
    if not ruta.is_file():
        return [f"falta {NOMBRE_ARCHIVO} (dedicatoria)"]
    mapa = cargar(raiz / "lecciones" / "mapa.yaml")
    return problemas_de_dedicatoria(ruta.read_text(encoding="utf-8"), mapa)
