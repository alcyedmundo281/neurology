"""Generador del proyecto Quarto (.qmd) del libro de Neurología (170 × 244 mm)."""

from __future__ import annotations

import shutil
import sys
import textwrap
from html import escape
from typing import TYPE_CHECKING

import yaml

from lecciones import dedicatoria
from lecciones.evidencia import cargar_articulos
from lecciones.fuente import leer as leer_leccion
from lecciones.mapa import cargar as cargar_mapa
from lecciones.proyectar import lecciones_por_parte, proyectar
from lecciones.semblanzas import renderizar as renderizar_semblanzas
from lecciones.semblanzas import verificar as verificar_semblanzas
from lecciones.validacion import claves_citadas
from libro import ALTO_MM, ALTO_PULGADAS, ANCHO_MM, ANCHO_PULGADAS
from libro.datos import (
    RAIZ,
    CondicionLibro,
    MetadatosLibro,
    fuentes_plataforma,
    leer_condiciones_neurologia,
    leer_metadatos,
    todos_los_hallazgos,
)
from libro.modulos import (
    CapituloModulo,
    obtener_banco_autoevaluacion,
    obtener_capitulos_modulos,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

RUTA_PREAMBULO = RAIZ / "assets" / "libro" / "preambulo.tex"
RUTA_FILTRO_LUA = RAIZ / "assets" / "libro" / "diseno-pdf.lua"
RUTA_FILTRO_TITULO = RAIZ / "assets" / "libro" / "quitar-titulo.lua"

NOMBRES_QMD_CONDICIONES: dict[str, str] = {
    "HM:6004": "01-hm6004-meningitis-aguda.qmd",
    "HM:6015": "02-hm6015-enfermedad-parkinson.qmd",
    "HM:6023": "03-hm6023-conmocion-cerebral-pediatrica.qmd",
    "HM:6038": "04-hm6038-traumatismo-craneal-leve.qmd",
}


def _lineas_autores(meta: MetadatosLibro) -> list[str]:
    """Una línea por autor, en el orden del mapa: nombre, función, afiliación y ORCID si existe."""
    lineas: list[str] = []
    for autor in meta.autores:
        detalle = [autor.rol] + ([autor.afiliacion] if autor.afiliacion else [])
        linea = f"**{autor.nombre_visible}** — {'; '.join(detalle)}"
        if autor.orcid:
            linea += f" · ORCID: <https://orcid.org/{autor.orcid}>"
        lineas.append(linea + "  ")
    return lineas


def _linea_autoevaluaciones(meta: MetadatosLibro) -> list[str]:
    """Quién escribe y quién revisa los bancos de preguntas de toda la obra (si el mapa lo dice)."""
    if not meta.autores_autoevaluaciones or meta.revisor_autoevaluaciones is None:
        return []
    return [
        f"**Autoevaluaciones:** {'; '.join(meta.autores_autoevaluaciones)}, de toda la obra. "
        f"Revisión: {meta.revisor_autoevaluaciones}.",
        "",
    ]


def _escapar_tex(texto: str) -> str:
    barra = chr(92)
    for caracter in "&%$#_{}":
        texto = texto.replace(caracter, barra + caracter)
    return texto


def _datos_libro_tex(meta: MetadatosLibro) -> str:
    """Macros de LaTeX con la autoría y el sello de la portada, generadas desde los datos."""
    barra = chr(92)
    nombres = (barra * 2 + " ").join(_escapar_tex(a.nombre_visible) for a in meta.autores)
    sello = (
        "Nueva edición "
        f"{barra}enspace·{barra}enspace {_escapar_tex(meta.licencia)}"
    )
    return (
        "% GENERADO por tools/libro/qmd.py desde lecciones/mapa.yaml. No editar a mano.\n"
        f"{barra}newcommand{{{barra}librotitulo}}{{{_escapar_tex(meta.titulo)}}}\n"
        f"{barra}newcommand{{{barra}librosubtitulo}}{{{_escapar_tex(meta.subtitulo)}}}\n"
        f"{barra}newcommand{{{barra}libroautoresportada}}{{{nombres}}}\n"
        f"{barra}newcommand{{{barra}librosellopie}}{{{sello}}}\n"
    )


def _generar_index_qmd(meta: MetadatosLibro, texto_dedicatoria: str) -> str:
    """Portada, portadilla, créditos, dedicatoria y tabla de contenidos: todo sale de los datos."""
    tamano_str = (
        f"{ANCHO_MM} × {ALTO_MM} mm ({ANCHO_PULGADAS:.2f} × {ALTO_PULGADAS:.2f} pulgadas)".replace(
            ".", ","
        )
    )

    lineas: list[str] = [
        "```{=latex}",
        "\\portadalibro",
        "```",
        "",
        "::: {.portadilla-pdf}",
        # Quarto abre el libro con la primera cabecera: la hace `\chapter*` y la pone antes de la
        # portada. `.titulo-de-obra` la marca para que quitar-titulo.lua la quite; el título que
        # se imprime en la portadilla es el bloque siguiente.
        f"# {meta.titulo} {{.unnumbered .unlisted .titulo-de-obra}}",
        "",
        "::: {.portadilla-titulo}",
        meta.titulo,
        ":::",
        "",
        f"*{meta.subtitulo}*",
        "",
        *[f"**{autor.nombre_visible}**  " for autor in meta.autores],
        ":::",
        "",
        "::: {.creditos-pdf}",
        f"**{meta.titulo}**  ",
        f"*{meta.subtitulo}*",
        "",
        f"Nueva edición, que continúa la obra de {meta.autores[0].nombre}:  ",
        *[f"· {obra}  " for obra in meta.obras_previas],
        "",
        "**Autoría:**  ",
        *_lineas_autores(meta),
        "",
        (
            f"**Revisión editorial:** {meta.editor.nombre}, editor, revisa todas las partes. "
            f"Es también autor de {'; '.join(meta.partes_del_editor)}: el editor es también "
            "autor; su revisión de esas partes no es independiente."
        ),
        "",
        *_linea_autoevaluaciones(meta),
        "Editor de la obra: pendiente del acuerdo escrito de los herederos.  ",
        "DOI de la obra: pendiente de asignación.  ",
        "ISBN: pendiente (reservado para la edición impresa).  ",
        f"Repositorio fuente: <{meta.url_repositorio}>  ",
        f"Plataforma complementaria: *medsemiotics*, <{meta.url_sitio}>  ",
        f"Comentarios, erratas y permisos: <{meta.contacto}>",
        "",
        (
            "**Fuente clínica única verificada:** las cifras de sensibilidad, especificidad y "
            "cocientes de verosimilitud (LR+ y LR−) proceden íntegramente de la base estructurada "
            "`medsemiotics-db`, a una revisión fijada, y de sus fuentes primarias indexadas en "
            "PubMed/DOI."
        ),
        "",
        (
            f"**Especificaciones de imprenta (catálogo KDP e IngramSpark):** formato de corte "
            f"{tamano_str}, composición tipográfica a dos caras en KOMA-Script (`scrbook` 10,5 pt) "
            "con la familia *Libertinus Serif* y motor LuaLaTeX."
        ),
        "",
        (
            f"**Licencia de publicación:** obra distribuida bajo licencia "
            f"**{meta.licencia_nombre} ({meta.licencia})**: uso, copia y adaptación libres con "
            "fines no comerciales; la explotación comercial queda reservada a los autores. "
            "Las imágenes clínicas registradas proceden de Wikimedia Commons en dominio público "
            "(PD) o dedicación CC0."
        ),
        "",
        "::: {.alerta-ficha}",
        "**Aviso médico-legal y docente:** Esta obra tiene carácter exclusivamente educativo y "
        "científico para estudiantes de medicina, residentes y profesionales de la salud. Ningún "
        "algoritmo, cociente de verosimilitud o protocolo sustituye el juicio clínico individual "
        "frente al paciente ni las guías oficiales de cada institución sanitaria.",
        ":::",
        ":::",
        "",
        "::: {.dedicatoria-pdf}",
        texto_dedicatoria.strip(),
        ":::",
        "",
        "```{=latex}",
        "\\tableofcontents",
        "\\cleardoublepage",
        "```",
        "",
    ]
    return "\n".join(lineas)


def _generar_prefacio_previo(
    condiciones: Sequence[CondicionLibro], modulos: Sequence[CapituloModulo]
) -> str:
    """Prefacio del material previo (con cifras de ejemplo escritas a mano: no es la obra)."""
    total_hallazgos = sum(len(c.articulo.evidencia) for c in condiciones)
    total_casos = sum(1 for c in condiciones if c.caso is not None)
    total_preguntas = len(obtener_banco_autoevaluacion())
    lineas: list[str] = [
        "# Prefacio y arquitectura metodológica {.unnumbered}",
        "",
        (
            "La neurología clínica es la disciplina médica donde la anamnesis dirigida y la "
            "exploración física conservan su mayor poder resolutivo. Sin embargo, durante décadas "
            "la enseñanza tradicional de la semiología neurológica transmitió maniobras epónimas "
            "sin explicitar su rendimiento diagnóstico cuantitativo real en estudios prospectivos. "
            "El proyecto **PowerSemiotics (`medsemiotics`)** une dos tradiciones complementarias: "
            "la **anatomía clínica localizadora** (que responde *dónde* se asienta la lesión) y "
            "la **medicina basada en la evidencia bayesiana** (que cuantifica *cuánto* modifica "
            "cada signo o regla de decisión la probabilidad de enfermedad)."
        ),
        "",
        "## Fundamento bayesiano de la semiología neurológica {.unnumbered}",
        "",
        (
            "Todo hallazgo semiológico actúa como una prueba diagnóstica que transforma una "
            "**probabilidad preprueba ($P_0$)** en una **probabilidad posprueba ($P_1$)** a través "
            "de sus **cocientes de verosimilitud (*likelihood ratios*, LR)**:"
        ),
        "",
        "$$",
        "\\text{Odds}_{\\text{posprueba}} = \\text{Odds}_{\\text{preprueba}} \\times \\text{LR}, "
        "\\qquad \\text{donde } \\text{Odds} = \\frac{P}{1 - P}",
        "$$",
        "",
        "$$",
        "\\text{LR}^+ = \\frac{\\text{Sensibilidad}}{1 - \\text{Especificidad}}, "
        "\\qquad "
        "\\text{LR}^- = \\frac{1 - \\text{Sensibilidad}}{\\text{Especificidad}}",
        "$$",
        "",
        (
            "- Un **$\\text{LR}^+ \\ge 10$** produce un incremento grande y a menudo concluyente "
            "en la probabilidad de la condición (por ejemplo, el cumplimiento de los criterios MDS "
            "para enfermedad de Parkinson clínicamente establecida con $\\text{LR}^+ = 24{,}5$)."
        ),
        (
            "- Un **$\\text{LR}^- \\le 0{,}10$** produce una reducción drástica que permite "
            "**descartar (*rule out*)** la condición con alto margen de seguridad (por ejemplo, "
            "la *Canadian CT Head Rule* negativa con $\\text{LR}^- = 0{,}04\\text{–}0{,}06$)."
        ),
        (
            "- Un **$\\text{LR}$ cercano a $1{,}0$** carece de poder discriminativo (por ejemplo, "
            "la ausencia aislada de los signos de Kernig o Brudzinski con $\\text{LR}^- = "
            "0{,}95\\text{–}0{,}97$, que jamás descarta una meningitis aguda)."
        ),
        "",
        "## Estructura de esta edición impresa {.unnumbered}",
        "",
        f"Esta obra integra **{len(condiciones)} condiciones verificadas** de `medsemiotics-db` "
        f"(con **{total_hallazgos} hallazgos semiológicos cuantificados** y **{total_casos} caso "
        f"socrático de aprendizaje basado en problemas**), **{len(modulos)} módulos clínicos "
        f"sistemáticos** y **{total_preguntas} problemas integradores de autoevaluación**:",
        "",
        (
            "1. **Parte I — Semiología Neurológica Basada en la Evidencia (`medsemiotics-db`) y "
            "Casos Socráticos:** aborda la meningitis aguda (`HM:6004`), la enfermedad de "
            "Parkinson según criterios MDS (`HM:6015`), la conmoción cerebral pediátrica y reglas "
            "PECARN (`HM:6023`), y la lesión intracraneal en el traumatismo craneal leve del "
            "adulto (`HM:6038`)."
        ),
        (
            "2. **Parte II — Síndromes Clínicos y Protocolos en Neurología:** desarrolla la "
            "exploración neurológica sistemática, cefaleas y banderas rojas SNOOP10, epilepsias y "
            "estado epiléptico, enfermedad cerebrovascular y Código Ictus, trastornos del "
            "movimiento hipo e hipercinéticos, enfermedades desmielinizantes del SNC, patología de "
            "la unión neuromuscular y miopatías, neuropatías periféricas y síndrome de "
            "Guillain-Barré, y demencias."
        ),
        (
            "3. **Apéndices:** banco de autoevaluación clínica integradora con justificación "
            "pedagógica detallada, índice maestro de precisión diagnóstica e inventario de "
            "iconografía abierta."
        ),
        "",
    ]
    return "\n".join(lineas)


def _generar_capitulo_condicion(cond: CondicionLibro) -> str:
    lineas: list[str] = [
        f"# {cond.titulo} (`{cond.condicion_id}`)",
        "",
        "::: {.enlace-ficha}",
        (
            f"**Condición verificada en `medsemiotics-db`:** `{cond.condicion_id}` · "
            f"Especialidad: {cond.especialidad} · Fecha de compilación: `{cond.fecha}` · "
            f"Archivo derivado: `posts/{cond.slug}.md`."
        ),
        ":::",
        "",
        cond.cuerpo_qmd.strip(),
        "",
    ]
    return "\n".join(lineas)


def _generar_capitulo_modulo(cap: CapituloModulo) -> str:
    lineas: list[str] = [
        f"# {cap.titulo}",
        "",
        f"*{cap.subtitulo}*",
        "",
        cap.cuerpo_qmd.strip(),
        "",
    ]
    return "\n".join(lineas)


def _generar_apendice_autoevaluacion() -> str:
    preguntas = obtener_banco_autoevaluacion()
    lineas: list[str] = [
        "# Autoevaluación Clínica Integradora y Respuestas Razonadas",
        "",
        (
            "Este apéndice reúne doce escenarios clínicos de selección múltiple extraídos de los "
            "módulos interactivos de evaluación del repositorio (`neurologia-autoevaluacion.html`, "
            "`cefaleas-autoevaluacion.html`, `epilepsia-2-autoevaluacion.html`, "
            "`neuromusculares.html` y `neuropatias.html`) y de las condiciones de "
            "`medsemiotics-db`. Se presenta primero el bloque de enunciados para resolución "
            "autónoma y, a continuación, la clave razonada."
        ),
        "",
        "## Enunciados de los casos clínicos",
        "",
    ]
    for p in preguntas:
        lineas.extend(
            [
                f"### Caso {p.numero}. {p.dominio}",
                "",
                p.enunciado,
                "",
            ]
        )
        for idx, op in enumerate(p.opciones):
            letra = chr(ord("A") + idx)
            lineas.append(f"- **{letra}.** {op}")
        lineas.append("")

    lineas.extend(
        [
            "---",
            "",
            "## Clave de respuestas y justificación fisiopatológica y bayesiana",
            "",
        ]
    )
    for p in preguntas:
        letra_ok = chr(ord("A") + p.indice_correcto)
        texto_ok = p.opciones[p.indice_correcto]
        lineas.extend(
            [
                "::: {.perlas-clinicas}",
                f"**Caso {p.numero} ({p.dominio}) — Respuesta correcta: {letra_ok}** "
                f"(*{texto_ok}*).",
                "",
                f"{p.justificacion}",
                "",
                f"*Fuente en el repositorio:* `{p.fuente}`.",
                ":::",
                "",
            ]
        )
    return "\n".join(lineas)


def _generar_apendice_evidencia(condiciones: Sequence[CondicionLibro]) -> str:
    filas = todos_los_hallazgos(list(condiciones))
    lineas: list[str] = [
        "# Síntesis de Evidencia Diagnóstica e Iconografía Abierta",
        "",
        "## Tabla maestra de hallazgos neurológicos (`medsemiotics-db`)",
        "",
        (
            "La siguiente tabla consolida los parámetros de sensibilidad, especificidad y "
            "cocientes de verosimilitud positivo ($\\text{LR}^+$) y negativo ($\\text{LR}^-$) de "
            "las condiciones neurológicas verificadas en la Parte I."
        ),
        "",
        "| Código | Condición | Signo, síntoma o regla | Sens. | Esp. | LR+ | LR− |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for h in filas:
        titulo_corto = h.titulo_condicion.split(":")[0].strip()
        lineas.append(
            f"| `{h.condicion_id}` | {titulo_corto} | {h.nombre} (`{h.hallazgo_id}`) | "
            f"{h.sensibilidad} | {h.especificidad} | {h.lr_pos} | {h.lr_neg} |"
        )
    lineas.extend(
        [
            "",
            ': {tbl-colwidths="[11,22,31,9,9,9,9]"}',
            "",
            "## Registro de iconografía clínica en dominio público (Wikimedia Commons)",
            "",
            (
                "Todas las imágenes asociadas a las condiciones neurológicas del repositorio han "
                "sido verificadas mediante `uv run python -m imagenes check` contra la API de "
                "Wikimedia Commons en dominio público (`pd`) o dedicación `cc0`:"
            ),
            "",
            "| Código | Archivo en Wikimedia Commons | Licencia | Autoría | Descripción clínica |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for cond in condiciones:
        if cond.imagen is not None:
            img = cond.imagen
            lineas.append(
                f"| `{cond.condicion_id}` | `{img.titulo_commons}` | {img.licencia} | "
                f"{img.autor} | {img.alt} |"
            )
    lineas.extend(
        [
            "",
            ': {tbl-colwidths="[11,26,13,20,30]"}',
            "",
        ]
    )
    return "\n".join(lineas)


def _tspans(texto: str, ancho: int, salto: int) -> list[str]:
    """Líneas de un texto de la portada SVG, partido entre palabras."""
    return [
        f'    <tspan x="164" dy="{0 if i == 0 else salto}">{escape(linea)}</tspan>'
        for i, linea in enumerate(textwrap.wrap(texto, ancho))
    ]


def _generar_portada_svg(meta: MetadatosLibro) -> str:
    """Genera portada vectorial SVG 1700 × 2440 (proporción exacta 170 × 244 mm)."""
    lineas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 1700 2440" width="170mm" height="244mm">',
        '  <rect width="1700" height="2440" fill="#0D1B2A" />',
        '  <rect x="96" y="96" width="1508" height="2248" fill="none" '
        'stroke="#F8F6F1" stroke-opacity="0.25" stroke-width="2" />',
        '  <rect x="114" y="114" width="1472" height="2212" fill="none" '
        'stroke="#C69C6D" stroke-opacity="0.55" stroke-width="3" />',
        '  <text x="164" y="210" fill="#C69C6D" '
        'font-family="Libertinus Sans, sans-serif" font-size="24" font-weight="bold">',
        "    MEDICINA BASADA EN LA EVIDENCIA",
        "  </text>",
        '  <line x1="164" y1="238" x2="820" y2="238" stroke="#C69C6D" stroke-width="3" />',
        '  <text x="164" y="345" fill="#F8F6F1" '
        'font-family="Libertinus Serif Display, serif" font-size="68" font-weight="bold">',
        *_tspans(meta.titulo, 26, 82),
        "  </text>",
        '  <text x="164" y="610" fill="#F8F6F1" fill-opacity="0.88" '
        'font-family="Libertinus Serif, serif" font-size="30" font-style="italic">',
        *_tspans(meta.subtitulo, 60, 42),
        "  </text>",
        '  <line x1="164" y1="705" x2="1536" y2="705" '
        'stroke="#C69C6D" stroke-opacity="0.65" stroke-width="2" />',
        '  <g transform="translate(850,1280)">',
        '    <circle cx="0" cy="0" r="390" fill="none" '
        'stroke="#F8F6F1" stroke-opacity="0.10" stroke-width="2" />',
        '    <circle cx="0" cy="0" r="280" fill="none" '
        'stroke="#C69C6D" stroke-opacity="0.30" stroke-width="3" stroke-dasharray="12,10" />',
        '    <circle cx="0" cy="0" r="160" fill="none" '
        'stroke="#F8F6F1" stroke-opacity="0.16" stroke-width="2" />',
        '    <polyline points="-380,30 -210,30 -175,-20 -140,60 -95,-220 '
        '-45,150 5,-45 55,30 380,30" '
        'fill="none" stroke="#C69C6D" stroke-width="6" />',
        "  </g>",
        '  <text x="164" y="2051" fill="#F8F6F1" '
        'font-family="Libertinus Sans, sans-serif" font-size="32" font-weight="bold">',
        *[
            f'    <tspan x="164" dy="{0 if i == 0 else 44}">{autor.nombre_visible}</tspan>'
            for i, autor in enumerate(meta.autores)
        ],
        "  </text>",
        '  <text x="164" y="2300" fill="#C69C6D" '
        'font-family="Libertinus Sans, sans-serif" font-size="24">',
        f"    Nueva edición · {meta.licencia}",
        "  </text>",
        "</svg>",
        "",
    ]
    return "\n".join(lineas)


def _configuracion_quarto(
    meta: MetadatosLibro,
    capitulos: list[object],
    con_bibliografia: bool = False,
) -> dict[str, object]:
    """``capitulos``: archivos y partes (``{"part": …, "chapters": […]}``) tras ``index.qmd``."""
    cfg: dict[str, object] = {
        "project": {
            "type": "book",
            "output-dir": "_book",
        },
        "book": {
            "title": meta.titulo,
            "subtitle": meta.subtitulo,
            "author": [autor.nombre_visible for autor in meta.autores],
            "output-file": "libro",
            "chapters": ["index.qmd", *capitulos],
        },
        "lang": "es",
        "format": {
            "pdf": {
                "documentclass": "scrbook",
                "classoption": ["twoside", "open=any", "fontsize=10.5pt"],
                "keep-tex": True,
                "pdf-engine": "lualatex",
                "toc": False,
                "number-sections": True,
                "colorlinks": True,
                "linkcolor": "libroprimario",
                "urlcolor": "libroacento",
                "citecolor": "libroprimario",
                "mainfont": "Libertinus Serif",
                "sansfont": "Libertinus Sans",
                "monofont": "Libertinus Mono",
                "geometry": [
                    f"paperwidth={ANCHO_MM}mm",
                    f"paperheight={ALTO_MM}mm",
                    "inner=20mm",
                    "outer=18mm",
                    "top=24mm",
                    "bottom=24mm",
                    "headsep=7mm",
                    "footskip=11mm",
                ],
                "include-in-header": ["datos-libro.tex", "preambulo-libro.tex"],
                "filters": ["diseno-pdf.lua", {"path": "quitar-titulo.lua", "at": "post-quarto"}],
            },
        },
    }
    if con_bibliografia:
        cfg["bibliography"] = "refs.bib"
    return cfg


def _capitulos_de_lecciones(
    carpeta_salida: Path,
    raiz: Path,
    generados: list[Path],
    secciones_planas: list[str],
    incluir_borradores: bool = False,
) -> tuple[list[dict[str, object]], list[str]]:
    """Lecciones de ``lecciones/`` proyectadas (tokens resueltos) como capítulos por parte."""
    articulos = cargar_articulos(raiz)
    partes: list[dict[str, object]] = []
    textos: list[str] = []
    for titulo, rutas in lecciones_por_parte(raiz, incluir_borradores):
        nombres: list[str] = []
        for ruta in rutas:
            nombre = f"L-{ruta.stem}.qmd"
            texto = proyectar(leer_leccion(ruta), articulos, "capitulo")
            (carpeta_salida / nombre).write_text(texto, encoding="utf-8")
            generados.append(carpeta_salida / nombre)
            secciones_planas.append(texto)
            textos.append(texto)
            nombres.append(nombre)
        partes.append({"part": titulo, "chapters": nombres})
    if not partes:
        print(
            "AVISO: ninguna lección está revisada o publicada; el libro sale sin ellas "
            "(--incluir-borradores las añade para una vista previa).",
            file=sys.stderr,
        )
    if partes:
        shutil.copyfile(raiz / "lecciones" / "refs.bib", carpeta_salida / "refs.bib")
        generados.append(carpeta_salida / "refs.bib")
    return partes, textos


def titulos_de_lecciones(raiz: Path = RAIZ, incluir_borradores: bool = False) -> list[str]:
    """Títulos de las lecciones que entran en el libro, en su orden."""
    return [
        str(leer_leccion(ruta).datos["titulo"])
        for _, rutas in lecciones_por_parte(raiz, incluir_borradores)
        for ruta in rutas
    ]


def _paratextos(
    carpeta_salida: Path,
    raiz: Path,
    textos_lecciones: list[str],
    generados: list[Path],
    secciones_planas: list[str],
) -> list[str]:
    """Paratextos de ``lecciones/paratextos/`` como capítulos finales sin numerar.

    ``{N}`` es el número de claves distintas citadas en las lecciones incluidas; su verificación
    contra PubMed y Crossref es ``lecciones citas``.
    """
    citadas = {c for texto in textos_lecciones for c in claves_citadas(texto)}
    nombres: list[str] = []
    for ruta in sorted((raiz / "lecciones" / "paratextos").glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        if ruta.name == "dedicatoria.md":  # va en el índice, tras los créditos, no al final
            continue
        if ruta.name == "autores.md":  # sin la aprobación y con los títulos del mapa
            texto = renderizar_semblanzas(texto, cargar_mapa(raiz / "lecciones" / "mapa.yaml"))
        texto = texto.replace("{N}", str(len(citadas)))
        nombre = f"P-{ruta.stem}.qmd"
        (carpeta_salida / nombre).write_text(texto, encoding="utf-8")
        generados.append(carpeta_salida / nombre)
        secciones_planas.append(texto)
        nombres.append(nombre)
    return nombres


PORTADA_MATERIAL_PREVIO = (
    "# Material previo — no forma parte de la obra {.unnumbered}\n\n"
    "::: {.alerta-ficha}\n"
    "**Material previo — no forma parte de la obra.** Lo que sigue (fichas de condiciones de "
    "`medsemiotics-db` y resúmenes de los módulos de clase) es el material con el que se empezó "
    "este libro. No está reconstruido como lección, no sigue la norma editorial y puede "
    "contradecirla. Se incluye solo como vista previa de trabajo.\n"
    ":::\n"
)


def _escribir(
    carpeta: Path, nombre: str, texto: str, generados: list[Path], planas: list[str]
) -> str:
    (carpeta / nombre).write_text(texto, encoding="utf-8")
    generados.append(carpeta / nombre)
    planas.append(texto)
    return nombre


def _material_previo(
    carpeta: Path, raiz: Path, generados: list[Path], planas: list[str]
) -> dict[str, object]:
    """Fichas de condiciones, resúmenes de módulos y apéndices anteriores a las lecciones."""
    condiciones = leer_condiciones_neurologia(raiz)
    modulos = obtener_capitulos_modulos()
    archivos = [
        _escribir(carpeta, "00-material-previo.qmd", PORTADA_MATERIAL_PREVIO, generados, planas),
        _escribir(
            carpeta,
            "00-prefacio-previo.qmd",
            _generar_prefacio_previo(condiciones, modulos),
            generados,
            planas,
        ),
    ]
    for cond in condiciones:
        nombre = NOMBRES_QMD_CONDICIONES[cond.condicion_id]
        archivos.append(
            _escribir(carpeta, nombre, _generar_capitulo_condicion(cond), generados, planas)
        )
    for mod in modulos:
        archivos.append(
            _escribir(carpeta, mod.archivo_qmd, _generar_capitulo_modulo(mod), generados, planas)
        )
    archivos.append(
        _escribir(
            carpeta, "14-autoevaluacion.qmd", _generar_apendice_autoevaluacion(), generados, planas
        )
    )
    archivos.append(
        _escribir(
            carpeta,
            "15-indice-evidencia-referencias.qmd",
            _generar_apendice_evidencia(condiciones),
            generados,
            planas,
        )
    )
    return {"part": "Material previo — no forma parte de la obra", "chapters": archivos}


def generar_proyecto_quarto(
    carpeta_salida: Path,
    raiz: Path = RAIZ,
    incluir_borradores: bool = False,
    material_previo: bool = False,
    exigir_semblanzas: bool = True,
) -> list[Path]:
    """Genera el proyecto Quarto del libro en ``carpeta_salida``.

    El libro se compone **solo de lecciones** (``lecciones/``, por parte del mapa, con sus tokens
    de evidencia resueltos contra ``posts/`` y ``lecciones/evidencia/``) y de sus paratextos
    (``lecciones/paratextos/``). Entran las lecciones revisadas o publicadas; ``incluir_borradores``
    añade las demás para una vista previa, cada una con el aviso «Borrador — sin revisión humana».
    ``material_previo`` añade, tras la obra y bajo una portada «Material previo — no forma parte de
    la obra», las fichas de condiciones y los resúmenes de módulos con los que se empezó.
    ``exigir_semblanzas`` (por defecto) detiene la compilación mientras «Sobre los autores» tenga
    una semblanza sin texto o sin aprobar por su titular, o la dedicatoria siga en propuesta; solo
    la vista previa y las pruebas la desactivan.
    """
    if exigir_semblanzas:
        avisos: list[str] = []
        if pendientes := verificar_semblanzas(raiz):
            avisos.append("«Sobre los autores» no está listo:\n- " + "\n- ".join(pendientes))
        if pendientes := dedicatoria.verificar(raiz):
            avisos.append("La dedicatoria no está lista:\n- " + "\n- ".join(pendientes))
        if avisos:
            raise ValueError("\n".join(avisos))
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    meta = leer_metadatos(raiz)

    shutil.copyfile(RUTA_PREAMBULO, carpeta_salida / "preambulo-libro.tex")
    (carpeta_salida / "datos-libro.tex").write_text(_datos_libro_tex(meta), encoding="utf-8")
    shutil.copyfile(RUTA_FILTRO_LUA, carpeta_salida / "diseno-pdf.lua")
    shutil.copyfile(RUTA_FILTRO_TITULO, carpeta_salida / "quitar-titulo.lua")

    ruta_portada_svg = carpeta_salida / "portada.svg"
    ruta_portada_svg.write_text(_generar_portada_svg(meta), encoding="utf-8")

    generados: list[Path] = [
        carpeta_salida / "preambulo-libro.tex",
        carpeta_salida / "datos-libro.tex",
        carpeta_salida / "diseno-pdf.lua",
        carpeta_salida / "quitar-titulo.lua",
        ruta_portada_svg,
    ]
    planas: list[str] = []
    ruta_dedicatoria = raiz.joinpath(*dedicatoria.RUTA)
    if not ruta_dedicatoria.is_file():
        raise FileNotFoundError(f"falta {dedicatoria.NOMBRE_ARCHIVO} (dedicatoria)")
    texto_dedicatoria = dedicatoria.renderizar(
        ruta_dedicatoria.read_text(encoding="utf-8"),
        cargar_mapa(raiz / "lecciones" / "mapa.yaml"),
    )
    _escribir(
        carpeta_salida, "index.qmd", _generar_index_qmd(meta, texto_dedicatoria), generados, planas
    )

    partes, textos = _capitulos_de_lecciones(
        carpeta_salida, raiz, generados, planas, incluir_borradores
    )
    capitulos: list[object] = [*partes]
    capitulos += _paratextos(carpeta_salida, raiz, textos, generados, planas)
    if material_previo:
        capitulos.append(_material_previo(carpeta_salida, fuentes_plataforma(), generados, planas))

    cfg = _configuracion_quarto(meta, capitulos, con_bibliografia=bool(partes))
    ruta_quarto_yml = carpeta_salida / "_quarto.yml"
    ruta_quarto_yml.write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    generados.append(ruta_quarto_yml)

    ruta_plano = carpeta_salida / "libro-plano.md"
    ruta_plano.write_text("\n\n---\n\n".join(planas), encoding="utf-8")
    generados.append(ruta_plano)
    return generados
