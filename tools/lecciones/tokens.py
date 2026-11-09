"""Tokens de evidencia de las lecciones: ``{{tipo HM:concepto>HM:condicion@n#t}}``.

Es la sintaxis de los casos (``casos.evidencia``) más un campo opcional: la condición. El
cociente pertenece a la arista concepto→condición, no al concepto: si el concepto figura en
una sola condición declarada por la lección, el token se resuelve contra ella; si figura en
varias, el token **debe** nombrar la condición (``{{lr+ HM:3240>HM:6004}}``). Un token que no
resuelve es un error, nunca texto crudo.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from casos.errores import ErrorDeCaso
from casos.evidencia import resolver_token

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from casos.articulo import Articulo

TOKEN = re.compile(
    r"\{\{\s*(?P<tipo>[a-z+\-]+)\s+(?P<id>HM:\d+)(?:>(?P<cond>HM:\d+))?"
    r"(?:@(?P<n>\d+))?(?:#(?P<t>\d+))?\s*\}\}"
)


class ErrorDeToken(ErrorDeCaso):
    """Un token de la lección no se puede resolver contra la evidencia sincronizada."""


def condicion_de(
    concepto: str,
    explicita: str | None,
    declaradas: Collection[str],
    articulos: Mapping[str, Articulo],
) -> Articulo:
    """El artículo cuya arista cita el token; falla si es ambigua, ajena o inexistente."""
    if explicita is not None:
        if explicita not in declaradas:
            raise ErrorDeToken(f"{concepto}>{explicita}: la lección no declara esa condición.")
        articulo = articulos.get(explicita)
        if articulo is None:
            raise ErrorDeToken(
                f"{concepto}>{explicita}: sin artículo en posts/ ni en lecciones/evidencia/."
            )
        if concepto not in articulo.evidencia:
            raise ErrorDeToken(f"{concepto} no está en la evidencia de {explicita}.")
        return articulo
    candidatas = [c for c in declaradas if c in articulos and concepto in articulos[c].evidencia]
    if not candidatas:
        raise ErrorDeToken(
            f"{concepto} no está en la evidencia de ninguna condición declarada "
            f"({', '.join(sorted(declaradas)) or 'ninguna'}); revise las fichas de evidencia"
        )
    if len(candidatas) > 1:
        opciones = ", ".join(f"{{{{lr+ {concepto}>{c}}}}}" for c in sorted(candidatas))
        raise ErrorDeToken(
            f"{concepto} figura en varias condiciones declaradas {sorted(candidatas)}: "
            f"nombre la condición del token, p. ej. {opciones}"
        )
    return articulos[candidatas[0]]


def resolver_token_leccion(
    m: re.Match[str], declaradas: Collection[str], articulos: Mapping[str, Articulo]
) -> str:
    articulo = condicion_de(m["id"], m["cond"], declaradas, articulos)
    return resolver_token(
        m["tipo"],
        m["id"],
        articulo,
        int(m["n"]) if m["n"] else None,
        int(m["t"]) if m["t"] else None,
    )


def problemas_de_tokens(
    texto: str, declaradas: Collection[str], articulos: Mapping[str, Articulo]
) -> list[str]:
    """Todos los tokens del texto que no resuelven, uno por problema (sin lanzar)."""
    problemas: list[str] = []
    for m in TOKEN.finditer(texto):
        try:
            resolver_token_leccion(m, declaradas, articulos)
        except ErrorDeCaso as exc:
            problemas.append(f"token {m[0]}: {exc}")
    return problemas


def resolver_texto(
    texto: str, declaradas: Collection[str], articulos: Mapping[str, Articulo]
) -> str:
    """Sustituye cada token por su valor; lanza ``ErrorDeToken`` agrupando todos los fallos."""
    problemas = problemas_de_tokens(texto, declaradas, articulos)
    if problemas:
        raise ErrorDeToken("\n".join(problemas))
    return TOKEN.sub(lambda m: resolver_token_leccion(m, declaradas, articulos), texto)
