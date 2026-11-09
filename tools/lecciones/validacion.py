"""Contrato editorial de una lección. No sustituye la revisión clínica humana.

Un ``borrador`` puede estar incompleto: sus faltas se informan como alertas. A partir de
``revisado`` cada falta bloquea. Un frontmatter que no se puede leer bloquea siempre.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import ValidationError

from casos.evidencia import LLAVES, PROHIBIDOS, TIPOS
from lecciones.fuente import RAIZ, ErrorDeFuente, leer, leer_bib
from lecciones.mapa import INDICE_MODULOS, modulos_publicados
from lecciones.modelo import Leccion
from lecciones.tokens import TOKEN

if TYPE_CHECKING:
    from pathlib import Path

    from lecciones.fuente import EntradaBib

# Plantilla de la lección (norma editorial: prólogos de 1993 + rigor de biosemiotics).
SECCIONES: tuple[str, ...] = (
    "Cómo se explora",
    "Qué significa",
    "Por qué ocurre",
    "Qué hacer",
    "Cómo prevenir",
    "Nuestra realidad",
)

PENDIENTE = re.compile(r"\b(TODO|PENDIENTE)\b")
# Grupo de citas Pandoc: [@a], [@a; @b], [véase @a, p. 3]. Cada clave se valida por separado.
GRUPO_CITAS = re.compile(r"\[[^\[\]]*@[^\[\]]*\]")
CLAVE_CITA = re.compile(r"@([A-Za-z][A-Za-z0-9_:\-]*)")
# Campos del frontmatter con prosa clínica: rigen las mismas reglas de evidencia que el cuerpo.
# La viñeta y la pregunta traen datos del paciente (edad, horas de vida), no afirmaciones de
# evidencia: en ellas las métricas siguen prohibidas, pero una cifra no exige cita.
CAMPOS_CLINICOS: tuple[str, ...] = (
    "pregunta_clinica",
    "abstract",
    "dialogo_clinico",
    "indispensable",
    "limites",
)
CAMPOS_CON_DATOS_DEL_PACIENTE: frozenset[str] = frozenset({"pregunta_clinica", "dialogo_clinico"})
DIGITO = re.compile(r"\d")
LISTA_NUMERADA = re.compile(r"^\s*\d+[.)]\s")
BLOQUE = re.compile(r"(?ms)^:::\s*\{\.(?P<clase>[a-z-]+)\}\s*$.*?^:::\s*$")
CODIGO = re.compile(r"(?ms)^(`{3,}|~{3,}).*?^\1\s*$")
COMENTARIO = re.compile(r"(?s)<!--.*?-->")
CODIGO_EN_LINEA = re.compile(r"`[^`\n]+`")


# Además de las de los casos: «LR positivo es 3,5», «el LR fue de 8».
PROHIBIDOS_LECCION: tuple[tuple[re.Pattern[str], str], ...] = (
    *PROHIBIDOS,
    (
        re.compile(r"\bLR\b[^.\n{]{0,25}?\d", re.I),
        "cociente de verosimilitud escrito a mano; use {{lr+ HM:…}} o {{lr- HM:…}}",
    ),
)


@dataclass
class Resultado:
    errores: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)


MARCA = chr(0)
CENTINELA = re.compile(re.escape(MARCA) + "([0-9]+)" + re.escape(MARCA))


def proteger(texto: str) -> tuple[str, list[str]]:
    """Sustituye el código y los comentarios por marcas; lo que queda es el texto que se escanea.

    Es la única definición de «texto escaneable»: ``lecciones check`` y la proyección la usan,
    así que un token dentro de código o de un comentario ni se comprueba ni se resuelve.
    """
    guardados: list[str] = []

    def guardar(m: re.Match[str]) -> str:
        guardados.append(m[0])
        return f"{MARCA}{len(guardados) - 1}{MARCA}"

    for patron in (CODIGO, COMENTARIO, CODIGO_EN_LINEA):
        texto = patron.sub(guardar, texto)
    return texto, guardados


def restaurar(texto: str, guardados: list[str]) -> str:
    while CENTINELA.search(texto):
        texto = CENTINELA.sub(lambda m: guardados[int(m[1])], texto)
    return texto


def _limpio(cuerpo: str) -> str:
    return CENTINELA.sub("", proteger(cuerpo)[0])


def problemas_de_cuerpo(cuerpo: str, leccion: Leccion | None) -> list[str]:
    """Secciones obligatorias, cifras sin token o sin cita, tokens fuera de la lección."""
    problemas: list[str] = []
    texto = _limpio(cuerpo)
    if PENDIENTE.search(texto):
        problemas.append("el cuerpo contiene TODO o PENDIENTE")

    encabezados = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", texto))
    for seccion in SECCIONES:
        indices = [i for i, h in enumerate(encabezados) if h[1] == seccion]
        if len(indices) != 1:
            problemas.append(f"## {seccion}: debe aparecer exactamente una vez")
            continue
        i = indices[0]
        fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(texto)
        contenido = re.sub(r"(?m)^#{1,6}\s+.*$", "", texto[encabezados[i].end() : fin])
        contenido = BLOQUE.sub("", contenido)
        if not contenido.strip():
            problemas.append(f"## {seccion}: sección vacía")

    clases = {m["clase"] for m in BLOQUE.finditer(texto)}
    if leccion is not None and leccion.legado is not None and "legado" not in clases:
        problemas.append("declara «legado» pero el cuerpo no tiene un bloque ::: {.legado}")

    # El bloque legado es una cita histórica literal: sus cifras no se reescriben ni se citan.
    prosa = BLOQUE.sub(lambda m: "" if m["clase"] == "legado" else m[0], texto)
    problemas += problemas_de_evidencia(prosa, leccion)
    return problemas


def claves_citadas(texto: str) -> list[str]:
    return [c for g in GRUPO_CITAS.findall(texto) for c in CLAVE_CITA.findall(g)]


def problemas_de_evidencia(
    prosa: str, leccion: Leccion | None, exigir_cita: bool = True
) -> list[str]:
    """Reglas de evidencia de toda prosa clínica, del cuerpo o del frontmatter.

    Las métricas de rendimiento solo entran por token; los tokens citan conceptos declarados;
    cualquier otra cifra va en un párrafo con cita, y cada clave citada está en «refs».
    """
    problemas: list[str] = []
    sin_tokens = TOKEN.sub(" ", prosa)
    malformado = LLAVES.search(sin_tokens)
    if malformado:
        problemas.append(f"token mal formado: {malformado[0]!r}")
    # Las claves de cita (p. ej. «[@futagi1999]») no son cifras del texto.
    sin_citas = GRUPO_CITAS.sub(" ", sin_tokens)
    for patron, motivo in PROHIBIDOS_LECCION:
        for m in patron.finditer(sin_citas):
            problemas.append(f"{motivo}: «{m[0]}»")

    declarados = set(leccion.conceptos) if leccion is not None else set()
    for m in TOKEN.finditer(prosa):
        if m["tipo"] not in TIPOS:
            problemas.append(f"token de tipo desconocido: {m[0]}")
        elif leccion is not None and m["id"] not in declarados:
            problemas.append(f"token {m[0]}: {m['id']} no figura en «conceptos»")
        if leccion is not None and m["cond"] and m["cond"] not in leccion.condiciones:
            problemas.append(f"token {m[0]}: {m['cond']} no figura en «condiciones»")

    refs = set(leccion.refs) if leccion is not None else set()
    for parrafo in re.split(r"\n\s*\n", sin_tokens):
        lineas = [
            LISTA_NUMERADA.sub("", ln)
            for ln in parrafo.splitlines()
            if not ln.lstrip().startswith(("#", ":::"))
        ]
        resto = GRUPO_CITAS.sub("", "\n".join(lineas))
        claves = claves_citadas(parrafo)
        if exigir_cita and DIGITO.search(resto) and not claves:
            extracto = " ".join(resto.split())[:70]
            problemas.append(f"cifra sin cita [@clave] en el párrafo: «{extracto}…»")
        for clave in claves:
            if leccion is not None and clave not in refs:
                problemas.append(f"cita [@{clave}] no declarada en «refs»")
    return problemas


def problemas_de_frontmatter(leccion: Leccion) -> list[str]:
    problemas: list[str] = []
    for campo in CAMPOS_CLINICOS:
        valor = getattr(leccion, campo)
        textos: list[str] = valor if isinstance(valor, list) else [valor]
        for texto in textos:
            exigir = campo not in CAMPOS_CON_DATOS_DEL_PACIENTE
            problemas += [f"{campo}: {p}" for p in problemas_de_evidencia(texto, leccion, exigir)]
    return problemas


def _textos(datos: object, ruta: str = "") -> list[tuple[str, str]]:
    """Pares (campo, texto) de todo el frontmatter, para buscar marcas sin redactar."""
    if isinstance(datos, str):
        return [(ruta, datos)]
    if isinstance(datos, dict):
        return [
            par for k, v in datos.items() for par in _textos(v, k if not ruta else f"{ruta}.{k}")
        ]
    if isinstance(datos, list):
        return [par for v in datos for par in _textos(v, ruta)]
    return []


def problemas_de_referencias(leccion: Leccion, bib: dict[str, EntradaBib]) -> list[str]:
    problemas: list[str] = []
    for clave in leccion.refs:
        entrada = bib.get(clave)
        if entrada is None:
            problemas.append(f"refs: «{clave}» no está en lecciones/refs.bib")
            continue
        if not re.fullmatch(r"[1-9]\d*", entrada.pmid):
            problemas.append(f"refs: «{clave}» sin PMID numérico en refs.bib")
        if not entrada.doi.startswith("10."):
            problemas.append(f"refs: «{clave}» sin DOI en refs.bib")
    return problemas


def problemas_de_archivos(leccion: Leccion, raiz: Path) -> list[str]:
    problemas: list[str] = []
    for medio in leccion.medios:
        if not (raiz / medio.archivo_local).is_file():
            problemas.append(f"medio {medio.id}: no existe {medio.archivo_local}")
    publicados = modulos_publicados(raiz / INDICE_MODULOS.relative_to(RAIZ))
    for modulo in leccion.modulos_html:
        if modulo not in publicados:
            problemas.append(f"modulos_html: no existe {modulo}")
    return problemas


def validar_archivo(
    ruta: Path, raiz: Path = RAIZ, bib: dict[str, EntradaBib] | None = None
) -> Resultado:
    resultado = Resultado()
    nombre = ruta.name
    try:
        archivo = leer(ruta)
        bib = leer_bib() if bib is None else bib
    except ErrorDeFuente as exc:
        resultado.errores.append(str(exc))
        return resultado

    borrador = archivo.datos.get("estado", "borrador") == "borrador"
    destino = resultado.alertas if borrador else resultado.errores

    try:
        leccion: Leccion | None = Leccion.model_validate(archivo.datos)
    except ValidationError as exc:
        leccion = None
        for e in exc.errors():
            lugar = ".".join(str(p) for p in e["loc"]) or "frontmatter"
            destino.append(f"{nombre}: {lugar}: {e['msg']}")

    marcas = sorted({clave for clave, valor in _textos(archivo.datos) if PENDIENTE.search(valor)})
    if marcas:
        destino.append(f"{nombre}: campos sin redactar (PENDIENTE/TODO): {', '.join(marcas)}")

    if leccion is not None:
        if ruta.stem != leccion.id:
            resultado.errores.append(f"{nombre}: el archivo debe llamarse {leccion.id}.qmd")
        destino.extend(f"{nombre}: {p}" for p in problemas_de_frontmatter(leccion))
        destino.extend(f"{nombre}: {p}" for p in problemas_de_referencias(leccion, bib))
        destino.extend(f"{nombre}: {p}" for p in problemas_de_archivos(leccion, raiz))

    destino.extend(f"{nombre}: {p}" for p in problemas_de_cuerpo(archivo.cuerpo, leccion))
    return resultado


DECLARACION = ("lecciones", "AI-USE.md")
COLOFON = ("lecciones", "paratextos", "declaracion-ia.md")


def problemas_de_declaracion(raiz: Path) -> list[str]:
    """La obra no sale sin su declaración de uso de IA ni su colofón (como biosemiotics)."""
    problemas: list[str] = []
    declaracion = raiz.joinpath(*DECLARACION)
    colofon = raiz.joinpath(*COLOFON)
    if not declaracion.is_file():
        problemas.append("falta lecciones/AI-USE.md: la obra no sale sin su declaración de IA")
    elif "## Qué ya falló" not in declaracion.read_text(encoding="utf-8"):
        problemas.append("lecciones/AI-USE.md debe documentar «## Qué ya falló»")
    if not colofon.is_file():
        problemas.append("falta lecciones/paratextos/declaracion-ia.md (colofón de cada edición)")
    elif "{N}" not in colofon.read_text(encoding="utf-8"):
        problemas.append("el colofón de IA debe llevar el marcador {N} de citas verificadas")
    return problemas


def validar_todo(rutas: list[Path], raiz: Path = RAIZ) -> Resultado:
    total = Resultado()
    total.errores.extend(problemas_de_declaracion(raiz))
    try:
        bib = leer_bib()
    except ErrorDeFuente as exc:
        total.errores.append(str(exc))
        return total
    ids: dict[str, str] = {}
    orden: dict[tuple[str, int], str] = {}
    for ruta in rutas:
        r = validar_archivo(ruta, raiz, bib)
        total.errores.extend(r.errores)
        total.alertas.extend(r.alertas)
        try:
            datos = leer(ruta).datos
        except ErrorDeFuente:
            continue
        ident, parte, num = datos.get("id"), datos.get("parte"), datos.get("orden")
        if isinstance(ident, str):
            if ident in ids:
                total.errores.append(f"id repetido «{ident}»: {ids[ident]} y {ruta.name}")
            ids[ident] = ruta.name
        if isinstance(parte, str) and isinstance(num, int):
            if (parte, num) in orden:
                previo = orden[(parte, num)]
                total.errores.append(
                    f"orden {num} repetido en la parte «{parte}»: {previo} y {ruta.name}"
                )
            orden[(parte, num)] = ruta.name
    return total
