"""Cotejo de cifras contra sus fuentes (requiere red; corre dentro de ``lecciones citas``).

``lecciones check`` exige que toda oración con una cifra lleve su cita, pero no puede saber si la
cita sostiene la cifra: una dosis o un porcentaje inventados pasarían con cualquier [@clave].
Aquí cada número de una oración citada se busca en el texto de las fuentes que esa oración cita:
el resumen de PubMed y, si no está ahí, el texto completo de PubMed Central cuando es abierto.

Una cifra que solo está en un texto completo cerrado se declara en el frontmatter de la lección,
en ``cifras_cotejadas`` (cifra, clave y ubicación en la fuente), como afirmación del revisor.

Una cifra no encontrada es un aviso en un borrador y una discrepancia desde ``revisado``.
Las cifras escritas con letras («un tercio», «seis meses») no se cotejan aquí.
"""

from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from lecciones.citas import EUTILS, RedNoDisponible, _texto
from lecciones.tokens import TOKEN
from lecciones.validacion import (
    BLOQUE,
    CAMPOS_CLINICOS,
    CAMPOS_CON_DATOS_DEL_PACIENTE,
    GRUPO_CITAS,
    LISTA_NUMERADA,
    _limpio,
    claves_citadas,
    oraciones,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from lecciones.fuente import Archivo

EFETCH = EUTILS.replace("esummary", "efetch")
NUMERO = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass(frozen=True)
class TextoFuente:
    resumen: str
    pmcid: str | None


@dataclass
class Cotejo:
    discrepancias: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    incompletas: list[str] = field(default_factory=list)


_UNIDADES = {
    w: i
    for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
        "fifteen sixteen seventeen eighteen nineteen".split()
    )
}
_DECENAS = {
    w: 10 * i
    for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split())
    if w != "_"
}
_PALABRA = "|".join([*_UNIDADES, *_DECENAS, "hundred", "thousand"])
EN_LETRAS = re.compile(rf"\b(?:{_PALABRA})(?:(?:[\s-]+|\s+and\s+)(?:{_PALABRA}))*\b", re.I)


def _valor_en_letras(frase: str) -> int:
    total = actual = 0
    for w in re.split(r"[\s-]+", frase.lower()):
        if w == "and":
            continue
        if w in _UNIDADES:
            actual += _UNIDADES[w]
        elif w in _DECENAS:
            actual += _DECENAS[w]
        elif w == "hundred":
            actual = max(actual, 1) * 100
        elif w == "thousand":
            total += max(actual, 1) * 1000
            actual = 0
    return total + actual


# En una fuente en inglés la coma entre dígitos agrupa miles («1,000», «14,145»); no es decimal.
MILES_EN = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")


def numeros_de_fuente(texto: str) -> set[str]:
    """Los números de una fuente en inglés: comas de miles quitadas y números con letras
    («Ninety-three») incluidos."""
    texto = MILES_EN.sub("", texto)
    return numeros(texto) | {str(_valor_en_letras(m[0])) for m in EN_LETRAS.finditer(texto)}


def numeros(texto: str) -> set[str]:
    """Números normalizados: coma decimal a punto, sin ceros finales tras el punto."""
    salida: set[str] = set()
    for n in NUMERO.findall(texto):
        n = n.replace(",", ".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        salida.add(n)
    return salida


def oraciones_con_cifras(archivo: Archivo) -> list[tuple[str, list[str]]]:
    """(oración, claves citadas) de toda prosa clínica con cifras, como la escanea ``check``."""
    textos: list[str] = []
    cuerpo = BLOQUE.sub(lambda m: "" if m["clase"] == "legado" else m[0], _limpio(archivo.cuerpo))
    textos.append(cuerpo)
    for campo in CAMPOS_CLINICOS:
        if campo in CAMPOS_CON_DATOS_DEL_PACIENTE:
            continue
        valor = archivo.datos.get(campo) or []
        textos += [v for v in (valor if isinstance(valor, list) else [valor]) if isinstance(v, str)]
    salida: list[tuple[str, list[str]]] = []
    for texto in textos:
        for parrafo in re.split(r"\n\s*\n", TOKEN.sub(" ", texto)):
            lineas = [
                LISTA_NUMERADA.sub("", ln)
                for ln in parrafo.splitlines()
                if not ln.lstrip().startswith(("#", ":::"))
            ]
            for oracion in oraciones("\n".join(lineas)):
                claves = claves_citadas(oracion)
                if claves and numeros(GRUPO_CITAS.sub(" ", oracion)):
                    salida.append((" ".join(oracion.split()), claves))
    return salida


def _xml(url: str) -> ET.Element:
    return ET.fromstring(_texto(url))


def resumenes_pubmed(pmids: list[str]) -> dict[str, TextoFuente]:
    if not pmids:
        return {}
    url = (
        EFETCH
        + "?"
        + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    )
    salida: dict[str, TextoFuente] = {}
    for art in _xml(url).iter("PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID") or ""
        partes = [art.findtext(".//ArticleTitle") or ""]
        partes += ["".join(a.itertext()) for a in art.iter("AbstractText")]
        pmc = next(
            (i.text for i in art.iter("ArticleId") if i.get("IdType") == "pmc" and i.text), None
        )
        salida[pmid] = TextoFuente(" ".join(partes), pmc)
    return salida


def texto_completo_pmc(pmcid: str) -> str:
    url = (
        EFETCH
        + "?"
        + urllib.parse.urlencode({"db": "pmc", "id": pmcid.removeprefix("PMC"), "retmode": "xml"})
    )
    return " ".join(_xml(url).itertext())


def cotejar(
    lecciones: list[Archivo],
    pmid_de: Mapping[str, str],
    consultar_resumenes: Callable[[list[str]], dict[str, TextoFuente]] = resumenes_pubmed,
    consultar_pmc: Callable[[str], str] = texto_completo_pmc,
) -> Cotejo:
    informe = Cotejo()
    claves = sorted({c for a in lecciones for _, cs in oraciones_con_cifras(a) for c in cs})
    pmids = sorted({pmid_de[c] for c in claves if c in pmid_de})
    try:
        resumenes = consultar_resumenes(pmids)
    except RedNoDisponible as exc:
        informe.incompletas.append(f"PubMed no disponible para el cotejo de cifras: {exc}")
        return informe
    completos: dict[str, set[str]] = {}

    def numeros_de(clave: str, completo: bool) -> set[str]:
        fuente = resumenes.get(pmid_de.get(clave, ""))
        if fuente is None:
            return set()
        if not completo or fuente.pmcid is None:
            return numeros_de_fuente(fuente.resumen)
        if clave not in completos:
            completos[clave] = numeros_de_fuente(consultar_pmc(fuente.pmcid))
        return completos[clave] | numeros_de_fuente(fuente.resumen)

    for archivo in lecciones:
        datos: dict[str, Any] = archivo.datos
        destino = (
            informe.avisos
            if datos.get("estado", "borrador") == "borrador"
            else (informe.discrepancias)
        )
        declaradas = [
            (numeros(str(c.get("cifra", ""))), c.get("clave"))
            for c in datos.get("cifras_cotejadas") or []
            if isinstance(c, dict)
        ]
        for oracion, cs in oraciones_con_cifras(archivo):
            faltan = numeros(GRUPO_CITAS.sub(" ", oracion))
            for ns, clave_declarada in declaradas:
                if clave_declarada in cs:
                    faltan -= ns
            for clave in cs:
                faltan -= numeros_de(clave, completo=False)
            if faltan:
                try:
                    for clave in cs:
                        faltan -= numeros_de(clave, completo=True)
                except RedNoDisponible as exc:
                    informe.incompletas.append(f"PMC no disponible: {exc}")
                    continue
            if faltan:
                destino.append(
                    f"{archivo.ruta.name}: {', '.join(sorted(faltan))} no aparece(n) en "
                    f"{', '.join(cs)}: «{oracion[:90]}…»"
                )
    return informe
