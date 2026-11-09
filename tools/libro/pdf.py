"""Compilación PDF con Quarto + LuaLaTeX y verificación técnica con pdfinfo."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from libro import (
    ALTO_MM,
    ALTO_PT,
    ALTO_PULGADAS,
    ANCHO_MM,
    ANCHO_PT,
    ANCHO_PULGADAS,
    CONDICIONES_NEUROLOGIA,
    TOLERANCIA_PT,
)
from libro.datos import RAIZ, fuentes_plataforma
from libro.modulos import obtener_capitulos_modulos, verificar_fuentes_neurologia
from libro.qmd import generar_proyecto_quarto, titulos_de_lecciones

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_PAGE_SIZE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*x\s*([0-9]+(?:\.[0-9]+)?)\s*pts")


@dataclass(frozen=True)
class InfoPDF:
    ruta: Path
    paginas: int
    ancho_pt: float
    alto_pt: float
    ancho_mm: float
    alto_mm: float
    ancho_in: float
    alto_in: float
    encriptado: str
    version_pdf: str
    productor: str
    tamano_bytes: int
    salida_bruta: str


def parsear_salida_pdfinfo(ruta_pdf: Path, texto: str, tamano_bytes: int = 0) -> InfoPDF:
    campos: dict[str, str] = {}
    for linea in texto.splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            campos[clave.strip()] = valor.strip()

    paginas_str = campos.get("Pages", "0")
    try:
        paginas = int(paginas_str)
    except ValueError as err:
        raise ValueError(f"pdfinfo: número de páginas inválido: {paginas_str!r}") from err

    page_size_raw = campos.get("Page size", "")
    match = _PAGE_SIZE_RE.search(page_size_raw)
    if not match:
        raise ValueError(f"pdfinfo: no se pudo extraer 'Page size' en puntos de: {page_size_raw!r}")

    ancho_pt = float(match.group(1))
    alto_pt = float(match.group(2))
    ancho_in = round(ancho_pt / 72.0, 2)
    alto_in = round(alto_pt / 72.0, 2)
    ancho_mm = round(ancho_pt * 25.4 / 72.0, 1)
    alto_mm = round(alto_pt * 25.4 / 72.0, 1)

    return InfoPDF(
        ruta=ruta_pdf,
        paginas=paginas,
        ancho_pt=ancho_pt,
        alto_pt=alto_pt,
        ancho_mm=ancho_mm,
        alto_mm=alto_mm,
        ancho_in=ancho_in,
        alto_in=alto_in,
        encriptado=campos.get("Encrypted", "no"),
        version_pdf=campos.get("PDF version", ""),
        productor=campos.get("Producer", ""),
        tamano_bytes=tamano_bytes,
        salida_bruta=texto,
    )


def inspeccionar_pdf_con_pdfinfo(ruta_pdf: Path) -> InfoPDF:
    """Ejecuta ``pdfinfo`` sobre ``ruta_pdf`` y devuelve sus metadatos estructurados."""
    if not ruta_pdf.is_file():
        raise FileNotFoundError(f"No existe el archivo PDF: {ruta_pdf}")
    ejecutable = shutil.which("pdfinfo")
    if ejecutable is None:
        raise RuntimeError("No se encontró la herramienta CLI 'pdfinfo' en el PATH.")

    resultado = subprocess.run(
        [ejecutable, str(ruta_pdf)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"pdfinfo falló ({resultado.returncode}): {resultado.stderr.strip()}")

    tamano = ruta_pdf.stat().st_size
    return parsear_salida_pdfinfo(ruta_pdf, resultado.stdout, tamano_bytes=tamano)


def paginas_minimas(material_previo: bool, lecciones: int) -> int:
    """Un libro sin lecciones ni material previo es solo portada, créditos y paratextos."""
    return 16 if material_previo or lecciones else 4


def validar_info_pdf(info: InfoPDF, paginas_minimas: int = 20) -> list[str]:
    """Verifica que las dimensiones y propiedades del PDF cumplan el catálogo 170 × 244 mm."""
    errores: list[str] = []
    if info.paginas < paginas_minimas:
        errores.append(
            f"El PDF tiene muy pocas páginas ({info.paginas}); se esperaban >= {paginas_minimas}."
        )
    if abs(info.ancho_pt - ANCHO_PT) > TOLERANCIA_PT:
        errores.append(
            f"Ancho de página incorrecto: {info.ancho_pt:.2f} pt ({info.ancho_mm:.1f} mm / "
            f"{info.ancho_in:.2f} in); se esperaban {ANCHO_PT:.2f} pt ({ANCHO_MM} mm / "
            f"{ANCHO_PULGADAS} in, catálogo KDP/IngramSpark)."
        )
    if abs(info.alto_pt - ALTO_PT) > TOLERANCIA_PT:
        errores.append(
            f"Alto de página incorrecto: {info.alto_pt:.2f} pt ({info.alto_mm:.1f} mm / "
            f"{info.alto_in:.2f} in); se esperaban {ALTO_PT:.2f} pt ({ALTO_MM} mm / "
            f"{ALTO_PULGADAS} in, catálogo KDP/IngramSpark)."
        )
    if not info.encriptado.lower().startswith("no"):
        errores.append(
            f"El PDF no debe estar encriptado para imprenta (Encrypted: {info.encriptado})."
        )
    if info.tamano_bytes <= 0:
        errores.append("El archivo PDF está vacío (0 bytes).")
    return errores


def validar_tex_libro(
    ruta_tex: Path,
    material_previo: bool = False,
    titulos_lecciones: Sequence[str] = (),
) -> list[str]:
    """Verifica la integridad estructural y tipográfica de ``libro.tex``.

    Exige los títulos de las lecciones incluidas; las condiciones y los capítulos de módulos del
    material previo solo se exigen si ``material_previo``.
    """
    if not ruta_tex.is_file():
        return [f"No se encontró el archivo LaTeX compilado: {ruta_tex}"]

    tex = ruta_tex.read_text(encoding="utf-8")
    errores: list[str] = []

    patrones_obligatorios: tuple[tuple[str, str], ...] = (
        (f"paperwidth={ANCHO_MM}mm", f"geometría de ancho {ANCHO_MM}mm"),
        (f"paperheight={ALTO_MM}mm", f"geometría de alto {ALTO_MM}mm"),
        (r"\portadalibro", "portada vectorial \\portadalibro"),
        (r"\begin{portadillapdf}", "entorno portadillapdf"),
        (r"\begin{creditospdf}", "entorno creditospdf"),
        (r"\begin{alertaficha}", "entorno alertaficha"),
        ("Libertinus Serif", "tipografía principal Libertinus Serif"),
    )
    if titulos_lecciones:
        patrones_obligatorios += (
            (r"\begin{casosocratico}", "entorno casosocratico"),
            (r"\begin{perlasclinicas}", "entorno perlasclinicas"),
        )
    for patron, descripcion in patrones_obligatorios:
        if patron not in tex:
            errores.append(f"libro.tex: falta {descripcion} ({patron!r}).")

    tex_normalizado = re.sub(r"\s+", " ", tex)
    for titulo in titulos_lecciones:
        if titulo not in tex_normalizado:
            errores.append(f"libro.tex: falta la lección {titulo!r}.")
    if material_previo:
        for cid in CONDICIONES_NEUROLOGIA:
            if cid not in tex:
                errores.append(f"libro.tex: falta la condición clínica {cid}.")
        for cap in obtener_capitulos_modulos():
            if cap.titulo not in tex_normalizado:
                errores.append(f"libro.tex: falta el capítulo {cap.titulo!r}.")
        if r"\part{Material previo --- no forma parte de la obra}" not in tex_normalizado:
            errores.append("libro.tex: falta la portada del material previo.")

    marcadores_rotos = ("[?]", "TODO", "FIXME")
    for marcador in marcadores_rotos:
        if marcador in tex:
            errores.append(f"libro.tex: contiene marcador sin resolver {marcador!r}.")

    return errores


def compilar_libro_pdf(
    ruta_salida: Path,
    carpeta_proyecto: Path,
    raiz: Path = RAIZ,
    incluir_borradores: bool = False,
    material_previo: bool = False,
    exigir_semblanzas: bool = True,
) -> InfoPDF:
    """Genera el proyecto Quarto, lo compila con LuaLaTeX y lo verifica con pdfinfo."""
    faltantes = verificar_fuentes_neurologia(fuentes_plataforma()) if material_previo else []
    if faltantes:
        raise FileNotFoundError(
            f"Faltan archivos fuente de neurología en el repositorio: {', '.join(faltantes)}"
        )

    for herramienta in ("quarto", "lualatex", "pdfinfo"):
        if shutil.which(herramienta) is None:
            raise RuntimeError(f"No se encontró '{herramienta}' en el PATH del sistema.")

    generar_proyecto_quarto(
        carpeta_proyecto,
        raiz=raiz,
        incluir_borradores=incluir_borradores,
        material_previo=material_previo,
        exigir_semblanzas=exigir_semblanzas,
    )

    ejecutable_quarto = shutil.which("quarto")
    assert ejecutable_quarto is not None
    resultado = subprocess.run(
        [ejecutable_quarto, "render", ".", "--to", "pdf"],
        cwd=carpeta_proyecto,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultado.returncode != 0:
        detalle = (resultado.stderr or resultado.stdout)[-4000:]
        raise RuntimeError(f"quarto render falló ({resultado.returncode}):\n{detalle}")

    pdf_generado = carpeta_proyecto / "_book" / "libro.pdf"
    if not pdf_generado.is_file():
        raise FileNotFoundError(f"Quarto no produjo el PDF esperado en {pdf_generado}")

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf_generado, ruta_salida)

    ruta_tex = carpeta_proyecto / "libro.tex"
    errores_tex = validar_tex_libro(
        ruta_tex, material_previo, titulos_de_lecciones(raiz, incluir_borradores)
    )
    if errores_tex:
        raise ValueError("\n".join(errores_tex))

    info = inspeccionar_pdf_con_pdfinfo(ruta_salida)
    titulos = titulos_de_lecciones(raiz, incluir_borradores)
    errores_pdf = validar_info_pdf(info, paginas_minimas(material_previo, len(titulos)))
    if errores_pdf:
        raise ValueError("\n".join(errores_pdf))

    return info
