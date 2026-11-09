"""«Sobre los autores» (``lecciones/paratextos/autores.md``): una semblanza por persona del mapa.

Cada semblanza la aprueba su titular antes de imprimirse; la de un autor fallecido la aprueban los
autores vivos. La aprobación vive en el frontmatter del paratexto (``aprobada_por`` y ``fecha``),
junto al texto, y la compilación del libro falla mientras falte alguna.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any

import yaml

from lecciones.mapa import cargar

if TYPE_CHECKING:
    from pathlib import Path

    from lecciones.mapa import Mapa

RUTA = ("lecciones", "paratextos", "autores.md")
NOMBRE_ARCHIVO = "lecciones/paratextos/autores.md"

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
# Cada semblanza es un div con el id de su persona; el título no se escribe: sale del mapa.
_SECCION = re.compile(r"^::: \{#sobre-([a-z]+)\}[ \t]*\n(.*?)^:::[ \t]*$", re.MULTILINE | re.DOTALL)


def separar(texto: str) -> tuple[dict[str, Any], str]:
    """Frontmatter YAML y cuerpo del paratexto (el frontmatter no se imprime en el libro)."""
    coincidencia = _FRONTMATTER.match(texto)
    if coincidencia is None:
        return {}, texto
    datos = yaml.safe_load(coincidencia.group(1))
    return (datos if isinstance(datos, dict) else {}), texto[coincidencia.end() :]


def _cuerpos(cuerpo: str) -> dict[str, str]:
    """Texto de cada semblanza por clave, en el orden en que aparece."""
    return {marca.group(1): marca.group(2).strip() for marca in _SECCION.finditer(cuerpo)}


def titulo_de(mapa: Mapa, clave: str) -> str:
    """Título de la semblanza: el nombre del mapa, con † si la persona falleció."""
    persona = mapa.personas[clave]
    return f"{persona.nombre} †" if persona.fallecido else persona.nombre


def renderizar(texto: str, mapa: Mapa) -> str:
    """El paratexto tal como se imprime: sin frontmatter y con cada título sacado del mapa."""
    cuerpo = separar(texto)[1]

    def seccion(marca: re.Match[str]) -> str:
        clave = marca.group(1)
        titulo = f"### {titulo_de(mapa, clave)} {{#sobre-{clave} .unnumbered}}"
        return f"{titulo}\n\n{marca.group(2).strip()}\n"

    return _SECCION.sub(seccion, cuerpo)


def _aprobadores(mapa: Mapa, clave: str) -> set[str]:
    """Quién tiene que aprobar la semblanza: su titular o, si falleció, los autores vivos."""
    if mapa.personas[clave].fallecido:
        return {k for k, p in mapa.personas.items() if not p.fallecido}
    return {clave}


def problemas_de_semblanzas(texto: str, mapa: Mapa) -> list[str]:
    """Defectos de ``autores.md``: orden, texto vacío y aprobaciones que faltan."""
    datos, cuerpo = separar(texto)
    esperadas = list(mapa.personas)
    problemas: list[str] = []
    registro = datos.get("semblanzas")
    if not isinstance(registro, dict) or list(registro) != esperadas:
        problemas.append(
            f"{NOMBRE_ARCHIVO}: el frontmatter debe listar `semblanzas` de {', '.join(esperadas)}, "
            "en el orden de autoría"
        )
        registro = {}
    cuerpos = _cuerpos(cuerpo)
    if list(cuerpos) != esperadas:
        problemas.append(
            f"{NOMBRE_ARCHIVO}: un bloque «::: {{#sobre-<clave>}}» por persona, en el orden "
            f"de autoría ({', '.join(esperadas)})"
        )
    for clave in esperadas:
        nombre = mapa.personas[clave].nombre
        ficha = registro.get(clave)
        if not isinstance(ficha, dict):
            continue
        if not cuerpos.get(clave):
            problemas.append(f"semblanza de {nombre}: sin texto")
        elif nombre not in cuerpos[clave]:
            problemas.append(
                f"semblanza de {nombre}: el texto debe nombrar a la persona como el mapa"
            )
        aprobada = ficha.get("aprobada_por") or []
        aprobada = {aprobada} if isinstance(aprobada, str) else set(aprobada)
        desconocidos = aprobada - set(mapa.personas)
        if desconocidos:
            problemas.append(
                f"semblanza de {nombre}: aprobada_por desconoce {sorted(desconocidos)}"
            )
        faltan = _aprobadores(mapa, clave) - aprobada
        if faltan:
            quienes = ", ".join(mapa.personas[k].nombre for k in sorted(faltan))
            problemas.append(f"semblanza de {nombre}: sin aprobar por {quienes}")
        elif not isinstance(ficha.get("fecha"), date):
            problemas.append(f"semblanza de {nombre}: falta la fecha de aprobación")
    return problemas


def verificar(raiz: Path) -> list[str]:
    """Problemas de ``autores.md`` de un repositorio (vacío: el paratexto puede imprimirse)."""
    ruta = raiz.joinpath(*RUTA)
    if not ruta.is_file():
        return [f"falta {NOMBRE_ARCHIVO} («Sobre los autores»)"]
    mapa = cargar(raiz / "lecciones" / "mapa.yaml")
    return problemas_de_semblanzas(ruta.read_text(encoding="utf-8"), mapa)
