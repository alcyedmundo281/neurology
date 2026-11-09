"""Pruebas unitarias y de integración del generador del libro de Neurología."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest
import yaml

from libro import (
    ALTO_MM,
    ALTO_PT,
    ALTO_PULGADAS,
    ANCHO_MM,
    ANCHO_PT,
    ANCHO_PULGADAS,
    CONDICIONES_NEUROLOGIA,
)
from libro import (
    __main__ as cli_libro,
)
from libro.datos import (
    RAIZ,
    fuentes_plataforma,
    leer_condiciones_neurologia,
    leer_imagenes_condiciones,
    leer_metadatos,
    todos_los_hallazgos,
)
from libro.modulos import (
    obtener_banco_autoevaluacion,
    obtener_capitulos_modulos,
    verificar_fuentes_neurologia,
)
from libro.pdf import (
    compilar_libro_pdf,
    parsear_salida_pdfinfo,
    validar_info_pdf,
    validar_tex_libro,
)
from libro.qmd import NOMBRES_QMD_CONDICIONES, generar_proyecto_quarto

if TYPE_CHECKING:
    from pathlib import Path


def test_dimensiones_catalogo_kdp_ingramspark() -> None:
    """Verifica que las dimensiones coincidan con el catálogo 6,69 × 9,61 in = 170 × 244 mm."""
    assert ANCHO_MM == 170
    assert ALTO_MM == 244
    assert pytest.approx(6.69, abs=0.01) == ANCHO_PULGADAS
    assert pytest.approx(9.61, abs=0.01) == ALTO_PULGADAS
    assert pytest.approx(170 * 72.0 / 25.4, abs=0.05) == ANCHO_PT
    assert pytest.approx(244 * 72.0 / 25.4, abs=0.05) == ALTO_PT


AUTORES_DEL_LIBRO = [
    "Alcy Torres Catefort †",
    "Alcy Ramiro Torres Guerrero",
    "Gladys Torres Guerrero",
    "Alcy Edmundo Torres Guerrero",
    "Daniela Torres Tobar",
]


@pytest.mark.skipif(not os.getenv("NEUROLOGY_MEDSEMIOTICS"), reason="requiere Medsemiotics")
def test_fuentes_y_condiciones_neurologia() -> None:
    assert verificar_fuentes_neurologia(fuentes_plataforma()) == []
    meta = leer_metadatos(RAIZ)
    assert "Neurología" in meta.titulo
    # Autoría y licencia salen de lecciones/mapa.yaml, en este orden; el libro aún no tiene DOI.
    assert meta.nombres_autores == AUTORES_DEL_LIBRO
    assert meta.licencia == "CC BY-NC-SA 4.0"
    assert not hasattr(meta, "doi")

    condiciones = leer_condiciones_neurologia(fuentes_plataforma())
    assert tuple(c.condicion_id for c in condiciones) == CONDICIONES_NEUROLOGIA
    # HM:6004 tiene caso socrático publicado e imagen verificada
    hm6004 = next(c for c in condiciones if c.condicion_id == "HM:6004")
    assert hm6004.caso is not None
    assert hm6004.imagen is not None
    assert ":::" in hm6004.cuerpo_qmd
    assert "Kernig" in hm6004.cuerpo_qmd

    filas = todos_los_hallazgos(condiciones)
    assert len(filas) >= 15

    imagenes = leer_imagenes_condiciones(fuentes_plataforma())
    for cid in CONDICIONES_NEUROLOGIA:
        assert cid in imagenes


def test_el_libro_por_defecto_solo_lleva_lecciones(tmp_path: Path) -> None:
    carpeta = tmp_path / "quarto"
    archivos = generar_proyecto_quarto(carpeta, raiz=RAIZ, exigir_semblanzas=False)
    for nombre in ("_quarto.yml", "index.qmd", "preambulo-libro.tex", "diseno-pdf.lua"):
        assert (carpeta / nombre).is_file()
    assert (carpeta / "portada.svg").is_file()
    assert (carpeta / "libro-plano.md").is_file()
    # Sin fichas de condiciones, resúmenes de módulos ni apéndices anteriores.
    for nombre_qmd in NOMBRES_QMD_CONDICIONES.values():
        assert not (carpeta / nombre_qmd).exists()
    for cap in obtener_capitulos_modulos():
        assert not (carpeta / cap.archivo_qmd).exists()
    assert not (carpeta / "14-autoevaluacion.qmd").exists()
    assert not (carpeta / "00-material-previo.qmd").exists()
    cfg = yaml.safe_load((carpeta / "_quarto.yml").read_text(encoding="utf-8"))
    assert "Material previo" not in str(cfg["book"]["chapters"])
    assert "Parte I" not in (carpeta / "libro-plano.md").read_text(encoding="utf-8")
    # El colofón de IA es un paratexto de lecciones/paratextos/, con {N} ya sustituido.
    colofon = (carpeta / "P-declaracion-ia.qmd").read_text(encoding="utf-8")
    assert "{N}" not in colofon
    assert "P-declaracion-ia.qmd" in cfg["book"]["chapters"]
    assert len(archivos) >= 6


@pytest.mark.skipif(not os.getenv("NEUROLOGY_MEDSEMIOTICS"), reason="requiere Medsemiotics")
def test_el_material_previo_va_aparte_con_su_portada(tmp_path: Path) -> None:
    carpeta = tmp_path / "quarto"
    archivos = generar_proyecto_quarto(
        carpeta, raiz=RAIZ, material_previo=True, exigir_semblanzas=False
    )
    assert len(archivos) >= 18
    assert (carpeta / "libro-plano.md").is_file()

    portada = (carpeta / "00-material-previo.qmd").read_text(encoding="utf-8")
    assert "Material previo — no forma parte de la obra" in portada
    cfg = yaml.safe_load((carpeta / "_quarto.yml").read_text(encoding="utf-8"))
    ultima = cfg["book"]["chapters"][-1]
    assert ultima["part"] == "Material previo — no forma parte de la obra"
    assert ultima["chapters"][0] == "00-material-previo.qmd"
    # Las lecciones y los paratextos van antes del material previo.
    assert "P-declaracion-ia.qmd" in cfg["book"]["chapters"][:-1]

    cfg = yaml.safe_load((carpeta / "_quarto.yml").read_text(encoding="utf-8"))
    geometria = cfg["format"]["pdf"]["geometry"]
    assert "paperwidth=170mm" in geometria
    assert "paperheight=244mm" in geometria
    assert cfg["format"]["pdf"]["pdf-engine"] == "lualatex"
    assert cfg["format"]["pdf"]["documentclass"] == "scrbook"

    for nombre_qmd in NOMBRES_QMD_CONDICIONES.values():
        assert (carpeta / nombre_qmd).is_file()

    for cap in obtener_capitulos_modulos():
        assert (carpeta / cap.archivo_qmd).is_file()

    assert len(obtener_banco_autoevaluacion()) == 12


def test_parsear_y_validar_pdfinfo_170x244(tmp_path: Path) -> None:
    ruta_pdf = tmp_path / "libro.pdf"
    salida_simulada = (
        "Title:          Neurología Clínica y Semiología Basada en la Evidencia\n"
        "Author:         Autor de prueba\n"
        "Producer:       LuaHBTeX-1.24.0\n"
        "Pages:          64\n"
        "Encrypted:      no\n"
        "Page size:      481.89 x 691.65 pts\n"
        "File size:      245120 bytes\n"
        "PDF version:    1.5\n"
    )
    info = parsear_salida_pdfinfo(ruta_pdf, salida_simulada, tamano_bytes=245120)
    assert info.paginas == 64
    assert info.ancho_mm == pytest.approx(170.0, abs=0.2)
    assert info.alto_mm == pytest.approx(244.0, abs=0.2)
    assert info.ancho_in == pytest.approx(6.69, abs=0.02)
    assert info.alto_in == pytest.approx(9.61, abs=0.02)
    assert validar_info_pdf(info) == []


def test_rechaza_dimensiones_fuera_de_catalogo(tmp_path: Path) -> None:
    ruta_pdf = tmp_path / "libro-170x240.pdf"
    # 170 x 240 mm = 481.89 x 680.31 pts (no existe en KDP/IngramSpark)
    salida_240 = (
        "Pages:          50\n"
        "Encrypted:      no\n"
        "Page size:      481.89 x 680.31 pts\n"
        "PDF version:    1.5\n"
    )
    info = parsear_salida_pdfinfo(ruta_pdf, salida_240, tamano_bytes=100000)
    errores = validar_info_pdf(info)
    assert any("Alto de página incorrecto" in e for e in errores)


def test_validar_tex_detecta_faltantes(tmp_path: Path) -> None:
    ruta_tex = tmp_path / "incompleto.tex"
    ruta_tex.write_text(r"\documentclass{scrbook}", encoding="utf-8")
    errores = validar_tex_libro(ruta_tex)
    assert any("paperwidth=170mm" in e for e in errores)
    assert any("paperheight=244mm" in e for e in errores)


@pytest.mark.skipif(not os.getenv("NEUROLOGY_MEDSEMIOTICS"), reason="requiere Medsemiotics")
def test_cli_qmd_y_check(tmp_path: Path) -> None:
    carpeta = tmp_path / "quarto_cli"
    with pytest.raises(ValueError, match="Sobre los autores"):
        cli_libro.main(["qmd", "--proyecto", str(carpeta)])
    rc_qmd = cli_libro.main(["qmd", "--proyecto", str(carpeta), "--semblanzas-pendientes"])
    assert rc_qmd == 0
    rc_check = cli_libro.main(
        ["check", "--proyecto", str(carpeta), "--pdf", str(tmp_path / "no-existe.pdf")]
    )
    assert rc_check == 0
    # Las fuentes del material previo solo se verifican si se pide.
    rc_previo = cli_libro.main(
        [
            "check",
            "--material-previo",
            "--proyecto",
            str(carpeta),
            "--pdf",
            str(tmp_path / "no-existe.pdf"),
        ]
    )
    assert rc_previo == 0
    rc_vista = cli_libro.main(
        [
            "qmd",
            "--proyecto",
            str(tmp_path / "vista"),
            "--incluir-borradores",
            "--material-previo",
            "--semblanzas-pendientes",
        ]
    )
    assert rc_vista == 0


def test_la_opcion_lecciones_ya_no_existe() -> None:
    with pytest.raises(SystemExit) as salida:
        cli_libro.main(["qmd", "--lecciones"])
    assert salida.value.code == 2


def test_los_roles_en_femenino_los_dice_el_mapa() -> None:
    roles = {a.nombre: a.rol for a in leer_metadatos(RAIZ).autores}
    assert roles["Gladys Torres Guerrero"] == "autora"
    assert roles["Daniela Torres Tobar"] == "autora de las autoevaluaciones"
    assert roles["Alcy Ramiro Torres Guerrero"] == "autor"


def test_los_creditos_dicen_autora_para_gtg_y_dtt(tmp_path: Path) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    assert "Gladys Torres Guerrero** — autora;" in index
    assert "Daniela Torres Tobar** — autora de las autoevaluaciones;" in index
    assert "Alcy Ramiro Torres Guerrero** — autor;" in index


def test_el_filtro_que_quita_el_titulo_de_capitulo_va_tras_los_de_quarto(tmp_path: Path) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    cfg = yaml.safe_load((tmp_path / "_quarto.yml").read_text(encoding="utf-8"))
    assert {"path": "quitar-titulo.lua", "at": "post-quarto"} in cfg["format"]["pdf"]["filters"]
    assert (tmp_path / "quitar-titulo.lua").is_file()


@pytest.mark.skipif(
    any(shutil.which(h) is None for h in ("quarto", "lualatex", "pdfinfo", "pdftotext")),
    reason="requiere quarto, lualatex y poppler",
)
def test_la_pagina_1_del_pdf_es_la_cubierta(tmp_path: Path) -> None:
    pdf = tmp_path / "libro.pdf"
    compilar_libro_pdf(pdf, tmp_path / "quarto", incluir_borradores=True, exigir_semblanzas=False)
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    pagina_1 = subprocess.run(
        [pdftotext, "-f", "1", "-l", "1", "-enc", "UTF-8", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    assert "COLECCIÓN POWERSEMIOTICS" in pagina_1
    assert "NUEVA EDICIÓN DE UNA OBRA FUNDADA EN 1991" in pagina_1
    assert "Neuroftalmología del niño y del adulto" in pagina_1


def test_la_portadilla_lleva_el_titulo_en_un_bloque_propio(tmp_path: Path) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    titulo = leer_metadatos(RAIZ).titulo
    portadilla = index.split("{.portadilla-pdf}")[1].split("{.creditos-pdf}")[0]
    assert f"::: {{.portadilla-titulo}}\n{titulo}\n:::" in portadilla
    # La cabecera que Quarto convierte en \chapter* se marca para quitarla; es otra cosa.
    assert "{.unnumbered .unlisted .titulo-de-obra}" in portadilla


@pytest.mark.skipif(
    any(shutil.which(h) is None for h in ("quarto", "lualatex", "pdfinfo", "pdftotext")),
    reason="requiere quarto, lualatex y poppler",
)
def test_la_portadilla_del_pdf_tiene_el_titulo_completo(tmp_path: Path) -> None:
    pdf = tmp_path / "libro.pdf"
    compilar_libro_pdf(pdf, tmp_path / "quarto", incluir_borradores=True, exigir_semblanzas=False)
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    paginas = [
        " ".join(
            subprocess.run(
                [pdftotext, "-f", str(n), "-l", str(n), "-enc", "UTF-8", str(pdf), "-"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout.split()
        )
        for n in (1, 2, 3)
    ]
    # Página 1 cubierta, 2 reverso en blanco, 3 portadilla con el título completo.
    assert "COLECCIÓN POWERSEMIOTICS" in paginas[0]
    assert paginas[1] == ""
    assert paginas[2].startswith(leer_metadatos(RAIZ).titulo)


# --- título y subtítulo: salen del mapa, en la cubierta y en la portadilla ---------------------


def _normal(texto: str) -> str:
    return " ".join(texto.split())


def _paginas_pdf(pdf: Path, hasta: int = 8) -> list[str]:
    pdftotext = shutil.which("pdftotext")
    assert pdftotext is not None
    return [
        _normal(
            subprocess.run(
                [pdftotext, "-f", str(n), "-l", str(n), "-enc", "UTF-8", str(pdf), "-"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout
        )
        for n in range(1, hasta + 1)
    ]


def test_el_titulo_de_la_obra_es_el_del_mapa() -> None:
    meta = leer_metadatos(RAIZ)
    assert meta.titulo == "Neurología clínica para el médico general"
    assert meta.subtitulo == "Semiología basada en la evidencia, del recién nacido al adulto"


def test_las_macros_de_cubierta_y_portadilla_salen_del_mapa(tmp_path: Path) -> None:
    meta = leer_metadatos(RAIZ)
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    datos = (tmp_path / "datos-libro.tex").read_text(encoding="utf-8")
    assert r"\newcommand{\librotitulo}{" + meta.titulo + "}" in datos
    assert r"\newcommand{\librosubtitulo}{" + meta.subtitulo + "}" in datos
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    portadilla = index.split("{.portadilla-pdf}")[1].split("{.creditos-pdf}")[0]
    assert f"# {meta.titulo} " in portadilla
    assert f"*{meta.subtitulo}*" in portadilla
    creditos = index.split("{.creditos-pdf}")[1]
    assert f"**{meta.titulo}**" in creditos
    assert f"*{meta.subtitulo}*" in creditos
    cfg = yaml.safe_load((tmp_path / "_quarto.yml").read_text(encoding="utf-8"))
    assert cfg["book"]["title"] == meta.titulo
    assert cfg["book"]["subtitle"] == meta.subtitulo
    svg = _normal((tmp_path / "portada.svg").read_text(encoding="utf-8"))
    assert all(palabra in svg for palabra in meta.titulo.split())


def test_ningun_titulo_escrito_a_mano() -> None:
    meta = leer_metadatos(RAIZ)
    antiguos = (
        "Semiología Basada en la Evidencia",
        "Cocientes de verosimilitud, reglas de decisión clínica",
        "Neurología Clínica y",
    )
    fuentes = [
        *(RAIZ / "tools" / "libro").glob("*.py"),
        *(RAIZ / "assets" / "libro").glob("*.tex"),
        *(RAIZ / "assets" / "libro").glob("*.lua"),
    ]
    for ruta in fuentes:
        texto = _normal(ruta.read_text(encoding="utf-8"))
        for cadena in (meta.titulo, meta.subtitulo, *antiguos):
            assert cadena not in texto, f"{ruta.name} escribe a mano «{cadena}»"


def test_la_declaracion_de_ia_nombra_la_obra_como_el_mapa() -> None:
    texto = (RAIZ / "lecciones" / "AI-USE.md").read_text(encoding="utf-8")
    assert f"*{leer_metadatos(RAIZ).titulo}*" in texto


@pytest.mark.skipif(
    any(shutil.which(h) is None for h in ("quarto", "lualatex", "pdfinfo", "pdftotext")),
    reason="requiere quarto, lualatex y poppler",
)
def test_cubierta_portadilla_y_metadatos_del_pdf_coinciden_con_el_mapa(tmp_path: Path) -> None:
    meta = leer_metadatos(RAIZ)
    pdf = tmp_path / "libro.pdf"
    info = compilar_libro_pdf(
        pdf, tmp_path / "quarto", incluir_borradores=True, exigir_semblanzas=False
    )
    paginas = _paginas_pdf(pdf)
    cubierta = next(p for p in paginas if "COLECCIÓN POWERSEMIOTICS" in p)
    assert meta.titulo in cubierta
    assert meta.subtitulo in cubierta
    # La portadilla abre con el título y trae los autores; los créditos añaden «Autoría:».
    portadilla = next(
        p for p in paginas if p.startswith(meta.titulo) and "Daniela" in p and "Autoría:" not in p
    )
    assert meta.subtitulo in portadilla
    titulo_pdf = next(ln for ln in info.salida_bruta.splitlines() if ln.startswith("Title:"))
    assert _normal(titulo_pdf.removeprefix("Title:")) == meta.titulo
