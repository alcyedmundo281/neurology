"""CLI del libro de Neurología: ``python -m libro <orden>``.

El libro se compone solo de lecciones (``lecciones/``) y sus paratextos. Entran las revisadas o
publicadas; ``--incluir-borradores`` añade los borradores (vista previa) y ``--material-previo``
las fichas de condiciones y los resúmenes de módulos anteriores, bajo su propia portada.

Órdenes disponibles:
- ``qmd``: genera el proyecto Quarto (`.qmd`, `_quarto.yml`, preámbulo LaTeX y filtro Lua)
  en ``build/quarto``.
- ``build``: genera el proyecto Quarto, compila el PDF con ``quarto`` + ``lualatex`` y
  verifica su geometría de catálogo KDP/IngramSpark (170 × 244 mm = 6,69 × 9,61 in) con
  ``pdfinfo``.
- ``check``: verifica autoría y lecciones (y, con ``--material-previo``, sus fuentes) y, si existe
  el PDF compilado, comprueba ``libro.tex`` y ``pdfinfo``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from libro import ALTO_MM, ALTO_PULGADAS, ANCHO_MM, ANCHO_PULGADAS
from libro.datos import RAIZ, fuentes_plataforma, leer_condiciones_neurologia, leer_metadatos
from libro.modulos import (
    obtener_banco_autoevaluacion,
    obtener_capitulos_modulos,
    verificar_fuentes_neurologia,
)
from libro.pdf import (
    compilar_libro_pdf,
    inspeccionar_pdf_con_pdfinfo,
    paginas_minimas,
    validar_info_pdf,
    validar_tex_libro,
)
from libro.qmd import generar_proyecto_quarto, titulos_de_lecciones

RUTA_PROYECTO_DEFECTO = RAIZ / "build" / "quarto"
RUTA_PDF_DEFECTO = RAIZ / "build" / "libro-neurologia.pdf"


def _imprimir_resumen_pdf(
    ruta_proyecto: Path,
    ruta_pdf: Path,
    incluir_borradores: bool = False,
    material_previo: bool = False,
) -> int:
    info = inspeccionar_pdf_con_pdfinfo(ruta_pdf)
    titulos = titulos_de_lecciones(RAIZ, incluir_borradores)
    errores = validar_info_pdf(info, paginas_minimas(material_previo, len(titulos)))
    ruta_tex = ruta_proyecto / "libro.tex"
    if ruta_tex.is_file():
        errores.extend(
            validar_tex_libro(
                ruta_tex, material_previo, titulos_de_lecciones(RAIZ, incluir_borradores)
            )
        )

    for err in errores:
        print(f"ERROR: {err}", file=sys.stderr)

    print(
        f"PDF verificado con pdfinfo: {info.ruta}\n"
        f"  Páginas       : {info.paginas}\n"
        f"  Page size (pt): {info.ancho_pt:.2f} × {info.alto_pt:.2f} pts\n"
        f"  Formato (mm)  : {info.ancho_mm:.1f} × {info.alto_mm:.1f} mm "
        f"(catálogo {ANCHO_MM} × {ALTO_MM} mm)\n"
        f"  Formato (in)  : {info.ancho_in:.2f} × {info.alto_in:.2f} in "
        f"(catálogo KDP / IngramSpark {ANCHO_PULGADAS} × {ALTO_PULGADAS} in)\n"
        f"  Versión PDF   : {info.version_pdf} · Encriptado: {info.encriptado}\n"
        f"  Tamaño archivo: {info.tamano_bytes:,} bytes"
    )
    return 1 if errores else 0


def _opciones_de_contenido(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--semblanzas-pendientes",
        action="store_true",
        help=(
            "Vista previa: permite compilar aunque «Sobre los autores» tenga semblanzas sin "
            "texto o sin aprobar por su titular, o la dedicatoria siga en propuesta (por defecto "
            "la compilación falla)."
        ),
    )
    parser.add_argument(
        "--incluir-borradores",
        action="store_true",
        help=(
            "Añade las lecciones en borrador (vista previa), cada una con el aviso "
            "«Borrador — sin revisión humana». Por defecto solo entran las revisadas o publicadas."
        ),
    )
    parser.add_argument(
        "--material-previo",
        action="store_true",
        help=(
            "Añade, tras la obra y bajo la portada «Material previo — no forma parte de la "
            "obra», las fichas de condiciones y los resúmenes de módulos previos a las lecciones."
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="libro",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="orden", required=True)

    p_qmd = sub.add_parser("qmd", help="Genera el proyecto Quarto (.qmd) en build/quarto.")
    p_qmd.add_argument(
        "--proyecto",
        type=Path,
        default=RUTA_PROYECTO_DEFECTO,
        help="Carpeta donde se escribe el proyecto Quarto (por defecto: build/quarto).",
    )

    _opciones_de_contenido(p_qmd)

    p_build = sub.add_parser(
        "build",
        help="Genera el proyecto Quarto, compila con lualatex y verifica con pdfinfo.",
    )
    p_build.add_argument(
        "--proyecto",
        type=Path,
        default=RUTA_PROYECTO_DEFECTO,
        help="Carpeta del proyecto Quarto (por defecto: build/quarto).",
    )
    p_build.add_argument(
        "--salida",
        type=Path,
        default=RUTA_PDF_DEFECTO,
        help="Ruta de salida del PDF compilado (por defecto: build/libro-neurologia.pdf).",
    )

    _opciones_de_contenido(p_build)

    p_check = sub.add_parser(
        "check",
        help="Valida fuentes, proyecto Quarto y (si existe) el PDF con pdfinfo.",
    )
    p_check.add_argument(
        "--proyecto",
        type=Path,
        default=RUTA_PROYECTO_DEFECTO,
        help="Carpeta del proyecto Quarto.",
    )
    p_check.add_argument(
        "--pdf",
        type=Path,
        default=RUTA_PDF_DEFECTO,
        help="Ruta del PDF a inspeccionar con pdfinfo.",
    )
    p_check.add_argument(
        "--exigir-pdf",
        action="store_true",
        help="Falla si el archivo PDF aún no ha sido compilado.",
    )
    _opciones_de_contenido(p_check)

    args = parser.parse_args(argv)

    if args.orden == "qmd":
        archivos = generar_proyecto_quarto(
            args.proyecto,
            raiz=RAIZ,
            incluir_borradores=args.incluir_borradores,
            material_previo=args.material_previo,
            exigir_semblanzas=not args.semblanzas_pendientes,
        )
        print(f"Proyecto Quarto generado en {args.proyecto} ({len(archivos)} archivos).")
        return 0

    if args.orden == "build":
        compilar_libro_pdf(
            args.salida,
            args.proyecto,
            raiz=RAIZ,
            incluir_borradores=args.incluir_borradores,
            material_previo=args.material_previo,
            exigir_semblanzas=not args.semblanzas_pendientes,
        )
        return _imprimir_resumen_pdf(
            args.proyecto, args.salida, args.incluir_borradores, args.material_previo
        )

    # orden == "check"
    titulos = titulos_de_lecciones(RAIZ, args.incluir_borradores)
    leer_metadatos(RAIZ)
    print(
        f"Libro solo de lecciones: {len(titulos)} lección(es) entran "
        + ("(con borradores)." if args.incluir_borradores else "(revisadas o publicadas).")
    )
    if args.material_previo:
        fuentes = fuentes_plataforma()
        faltantes = verificar_fuentes_neurologia(fuentes)
        if faltantes:
            for f in faltantes:
                print(f"ERROR: falta fuente de neurología: {f}", file=sys.stderr)
            return 1
        condiciones = leer_condiciones_neurologia(fuentes)
        modulos = obtener_capitulos_modulos()
        preguntas = obtener_banco_autoevaluacion()
        print(
            f"Material previo verificado: {len(condiciones)} condiciones de medsemiotics-db, "
            f"{len(modulos)} capítulos de módulos clínicos y {len(preguntas)} casos de "
            "autoevaluación."
        )

    if args.pdf.is_file():
        return _imprimir_resumen_pdf(
            args.proyecto, args.pdf, args.incluir_borradores, args.material_previo
        )
    if args.exigir_pdf:
        print(f"ERROR: no existe el PDF compilado en {args.pdf}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
