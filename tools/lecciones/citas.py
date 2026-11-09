"""Verificación de doble autoridad de ``lecciones/refs.bib`` (adaptada de biosemiotics).

No basta con que la clave exista (eso lo mira ``check``). Aquí se comprueba que cada entrada
siga siendo real y coherente contra dos fuentes independientes:

- PubMed, por PMID: la entrada existe y su DOI coincide con el declarado.
- Crossref, por DOI: el DOI resuelve y coincide con el que devuelve PubMed.

Un DOI que Crossref dice no conocer (400/404/422) es una verificación fallida, no un
problema de red. Un fallo transitorio (timeout, 429, 5xx) deja la verificación incompleta.

Códigos de salida: 0 todo verificado · 1 discrepancia o entrada inválida · 2 incompleta.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from lecciones.fuente import EntradaBib

UA = {"User-Agent": "medsemiotics-lecciones/1.0 (mailto:alcy.torres@powersemiotics.com)"}
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


class RedNoDisponible(Exception):
    """Fallo transitorio: no demuestra nada sobre la referencia."""


class DoiNoResuelve(Exception):
    def __init__(self, codigo: int) -> None:
        self.codigo = codigo
        super().__init__(f"HTTP {codigo}")


@dataclass(frozen=True)
class Registro:
    doi: str
    titulo: str


@dataclass
class Informe:
    verificadas: list[str] = field(default_factory=list)
    discrepancias: list[str] = field(default_factory=list)
    incompletas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def codigo(self) -> int:
        if self.discrepancias:
            return 1
        return 2 if self.incompletas else 0


def _json(url: str) -> Any:
    try:
        peticion = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(peticion, timeout=25) as respuesta:
            return json.loads(respuesta.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 404, 422) and "crossref" in url:
            raise DoiNoResuelve(exc.code) from exc
        raise RedNoDisponible(f"HTTP {exc.code}") from exc
    except (OSError, ValueError) as exc:
        raise RedNoDisponible(str(exc)) from exc


def pubmed(pmids: list[str]) -> dict[str, Registro]:
    """Resumen de PubMed por lote. Un PMID ausente del resultado no existe."""
    if not pmids:
        return {}
    url = (
        EUTILS
        + "?"
        + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
    )
    datos = _json(url).get("result", {})
    salida: dict[str, Registro] = {}
    for pmid in pmids:
        item = datos.get(pmid)
        if not isinstance(item, dict) or item.get("error"):
            continue
        doi = next(
            (i.get("value", "") for i in item.get("articleids", []) if i.get("idtype") == "doi"),
            "",
        )
        salida[pmid] = Registro(doi=str(doi), titulo=str(item.get("title", "")))
    return salida


def crossref(doi: str) -> Registro:
    mensaje = _json("https://api.crossref.org/works/" + urllib.parse.quote(doi)).get("message")
    if not isinstance(mensaje, dict) or not mensaje.get("DOI"):
        raise RedNoDisponible("respuesta de Crossref sin DOI")
    titulos = mensaje.get("title") or [""]
    return Registro(doi=str(mensaje["DOI"]), titulo=str(titulos[0]))


def _norma(texto: str) -> str:
    principal = re.sub(r"<[^>]+>", "", texto).split(".", 1)[0]
    return " ".join(re.sub(r"[^a-z0-9]+", " ", principal.lower()).split())


def verificar(
    bib: dict[str, EntradaBib],
    consultar_pubmed: Callable[[list[str]], dict[str, Registro]] = pubmed,
    consultar_crossref: Callable[[str], Registro] = crossref,
    pausa: float = 0.12,
) -> Informe:
    informe = Informe()
    invalidas = [c for c, e in bib.items() if not e.pmid.isdigit() or not e.doi.startswith("10.")]
    for clave in invalidas:
        informe.discrepancias.append(f"{clave}: falta PMID numérico o DOI")
    validas = {c: e for c, e in bib.items() if c not in invalidas}
    try:
        pm = consultar_pubmed([e.pmid for e in validas.values()])
    except RedNoDisponible as exc:
        informe.incompletas.append(f"PubMed no disponible: {exc}")
        return informe

    for clave, entrada in validas.items():
        registro = pm.get(entrada.pmid)
        if registro is None:
            informe.discrepancias.append(f"{clave}: PMID {entrada.pmid} no existe en PubMed")
            continue
        declarado = entrada.doi.lower()
        if registro.doi.lower() != declarado:
            informe.discrepancias.append(
                f"{clave}: DOI declarado {entrada.doi} ≠ PubMed {registro.doi or '∅'}"
            )
            continue
        try:
            cr = consultar_crossref(entrada.doi)
        except DoiNoResuelve as exc:
            informe.discrepancias.append(f"{clave}: Crossref no resuelve {entrada.doi} ({exc})")
            continue
        except RedNoDisponible as exc:
            informe.incompletas.append(f"{clave}: Crossref no disponible ({exc})")
            break
        if cr.doi.lower() != declarado:
            informe.discrepancias.append(f"{clave}: Crossref devuelve {cr.doi}")
            continue
        if (
            _norma(cr.titulo)
            and _norma(registro.titulo)
            and not (
                _norma(cr.titulo).startswith(_norma(registro.titulo)[:40])
                or _norma(registro.titulo).startswith(_norma(cr.titulo)[:40])
            )
        ):
            informe.avisos.append(f"{clave}: el título difiere entre PubMed y Crossref")
        informe.verificadas.append(clave)
        if pausa:
            time.sleep(pausa)
    return informe
