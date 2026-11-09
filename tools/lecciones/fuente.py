"""Lectura de ``lecciones/*.qmd`` y de ``lecciones/refs.bib``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "lecciones"
BIB = CARPETA / "refs.bib"

FRONTMATTER = re.compile(r"\A---\r?\n(?P<yaml>.*?)\r?\n---\r?\n(?P<cuerpo>.*)\Z", re.S)


@dataclass(frozen=True)
class Archivo:
    ruta: Path
    datos: dict[str, Any]
    cuerpo: str


@dataclass(frozen=True)
class EntradaBib:
    clave: str
    pmid: str
    doi: str
    titulo: str


class ErrorDeFuente(Exception):
    """El archivo no tiene la forma mínima para validarlo."""


def leer(ruta: Path) -> Archivo:
    texto = ruta.read_text(encoding="utf-8")
    m = FRONTMATTER.match(texto)
    if m is None:
        raise ErrorDeFuente(f"{ruta.name}: falta el frontmatter YAML entre líneas ---")
    try:
        datos = yaml.safe_load(m["yaml"])
    except yaml.YAMLError as exc:
        raise ErrorDeFuente(f"{ruta.name}: YAML inválido: {exc}") from exc
    if not isinstance(datos, dict):
        raise ErrorDeFuente(f"{ruta.name}: el frontmatter debe ser un diccionario")
    return Archivo(ruta=ruta, datos=datos, cuerpo=m["cuerpo"])


def archivos(carpeta: Path = CARPETA) -> list[Path]:
    """Lecciones en orden de nombre. Los archivos que empiezan por ``_`` no son lecciones."""
    if not carpeta.is_dir():
        return []
    return sorted(p for p in carpeta.glob("*.qmd") if not p.name.startswith("_"))


def _campo(cuerpo: str, nombre: str) -> str:
    m = re.search(nombre + r"\s*=\s*\{(.*?)\}\s*,?\s*$", cuerpo, re.S | re.M | re.I)
    return " ".join(m[1].split()) if m else ""


def leer_bib(ruta: Path = BIB) -> dict[str, EntradaBib]:
    """Bibliografía BibLaTeX mínima: ``@article{clave, pmid = {…}, doi = {…}, title = {…}}``.

    Una clave repetida o una entrada que no se puede leer es un error, no un aviso.
    """
    if not ruta.is_file():
        return {}
    texto = ruta.read_text(encoding="utf-8")
    cabeceras = re.findall(r"@\w+\s*\{", texto)
    entradas = re.findall(r"@article\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", texto, re.S)
    if len(cabeceras) != len(entradas):
        raise ErrorDeFuente(f"{ruta.name}: solo se admiten entradas @article bien cerradas")
    salida: dict[str, EntradaBib] = {}
    for clave, cuerpo in entradas:
        if clave in salida:
            raise ErrorDeFuente(f"{ruta.name}: clave repetida: {clave}")
        salida[clave] = EntradaBib(
            clave=clave,
            pmid=_campo(cuerpo, "pmid"),
            doi=_campo(cuerpo, "doi"),
            titulo=_campo(cuerpo, "title"),
        )
    return salida
