"""«Sobre los autores»: una semblanza por persona, aprobada por su titular antes de imprimirse."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest

from lecciones import mapa as m
from lecciones.semblanzas import (
    problemas_de_semblanzas,
    renderizar,
    separar,
    titulo_de,
    verificar,
)
from libro.datos import RAIZ
from libro.qmd import generar_proyecto_quarto

if TYPE_CHECKING:
    from pathlib import Path

CLAVES = ["atc", "artg", "gtg", "aetg", "dtt"]
VIVOS = ["artg", "gtg", "aetg", "dtt"]
FECHA = "2026-11-03"
PARATEXTO = RAIZ / "lecciones" / "paratextos" / "autores.md"


def _texto(aprobaciones: dict[str, tuple[list[str], str]], cuerpos: dict[str, str]) -> str:
    registro = "\n".join(
        f"  {k}: {{aprobada_por: {aprobaciones.get(k, ([], 'null'))[0]}, "
        f"fecha: {aprobaciones.get(k, ([], 'null'))[1]}}}"
        for k in CLAVES
    )
    bloques = "\n\n".join(f"::: {{#sobre-{k}}}\n{cuerpos.get(k, '')}\n:::" for k in CLAVES)
    encabezado = "## SOBRE LOS AUTORES {.unnumbered}"
    return f"---\nsemblanzas:\n{registro}\n---\n\n{encabezado}\n\n{bloques}\n"


def _completo() -> str:
    mapa = m.cargar()
    aprobaciones = {k: ([k], FECHA) for k in VIVOS} | {"atc": (VIVOS, FECHA)}
    cuerpos = {k: f"{mapa.personas[k].nombre} es una persona de prueba." for k in CLAVES}
    return _texto(aprobaciones, cuerpos)


def test_el_orden_del_paratexto_es_el_de_autoria() -> None:
    assert list(m.cargar().personas) == CLAVES


def test_la_semblanza_de_gtg_esta_pendiente_de_su_aprobacion() -> None:
    datos, cuerpo = separar(PARATEXTO.read_text(encoding="utf-8"))
    assert datos["semblanzas"]["gtg"] == {"aprobada_por": [], "fecha": None}
    assert "directora ejecutiva de VisionUno, en Quito" in cuerpo
    assert "Bascom Palmer" in cuerpo
    # Las demás siguen vacías hasta que las envíen sus titulares.
    for clave in ("atc", "artg", "aetg", "dtt"):
        assert f"::: {{#sobre-{clave}}}\n:::" in cuerpo


def test_el_nombre_de_la_semblanza_coincide_con_el_del_mapa() -> None:
    mapa = m.cargar()
    texto = PARATEXTO.read_text(encoding="utf-8")
    impreso = renderizar(texto, mapa)
    for clave in CLAVES:
        assert f"### {titulo_de(mapa, clave)} {{#sobre-{clave} .unnumbered}}" in impreso
    assert titulo_de(mapa, "atc") == "Alcy Torres Catefort †"
    # El texto de gtg usa el nombre del mapa, sin guion; la forma con guion es solo para citas.
    assert "Gladys Torres Guerrero es oftalmóloga" in impreso
    assert "Torres-Guerrero" not in impreso
    assert "aprobada_por" not in impreso


def test_el_texto_debe_nombrar_a_la_persona_como_el_mapa() -> None:
    texto = _completo().replace("Gladys Torres Guerrero es", "Gladys Torres-Guerrero es")
    assert problemas_de_semblanzas(texto, m.cargar()) == [
        "semblanza de Gladys Torres Guerrero: el texto debe nombrar a la persona como el mapa"
    ]


def test_afiliacion_de_gtg_en_el_mapa() -> None:
    assert m.cargar().personas["gtg"].afiliacion == "VisionUno, Quito"


def test_el_paratexto_del_repositorio_aun_no_se_puede_imprimir() -> None:
    problemas = verificar(RAIZ)
    assert any("Gladys Torres Guerrero" in p and "sin aprobar" in p for p in problemas)
    assert any("Daniela Torres Tobar" in p and "sin texto" in p for p in problemas)


def test_un_paratexto_completo_y_aprobado_no_da_problemas() -> None:
    assert problemas_de_semblanzas(_completo(), m.cargar()) == []


def test_la_de_un_autor_vivo_la_aprueba_su_titular_y_no_otro() -> None:
    texto = _completo().replace("gtg: {aprobada_por: ['gtg']", "gtg: {aprobada_por: ['aetg']")
    assert problemas_de_semblanzas(texto, m.cargar()) == [
        "semblanza de Gladys Torres Guerrero: sin aprobar por Gladys Torres Guerrero"
    ]


def test_la_de_atc_la_aprueban_todos_los_autores_vivos() -> None:
    texto = _completo().replace(
        "atc: {aprobada_por: ['artg', 'gtg', 'aetg', 'dtt']", "atc: {aprobada_por: ['artg', 'aetg']"
    )
    (problema,) = problemas_de_semblanzas(texto, m.cargar())
    assert "Alcy Torres Catefort" in problema
    assert "Gladys Torres Guerrero" in problema
    assert "Daniela Torres Tobar" in problema


def test_aprobar_sin_fecha_no_basta() -> None:
    antes = f"dtt: {{aprobada_por: ['dtt'], fecha: {FECHA}}}"
    texto = _completo().replace(antes, "dtt: {aprobada_por: ['dtt'], fecha: null}")
    assert problemas_de_semblanzas(texto, m.cargar()) == [
        "semblanza de Daniela Torres Tobar: falta la fecha de aprobación"
    ]


def test_el_orden_de_los_bloques_se_comprueba() -> None:
    texto = _completo().replace("#sobre-artg", "#sobre-tmp").replace("#sobre-gtg", "#sobre-artg")
    texto = texto.replace("#sobre-tmp", "#sobre-gtg")
    assert any("en el orden de autoría" in p for p in problemas_de_semblanzas(texto, m.cargar()))


def test_la_compilacion_falla_mientras_haya_semblanzas_sin_aprobar(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Sobre los autores"):
        generar_proyecto_quarto(tmp_path, RAIZ)


def test_aprobado_el_paratexto_se_imprime_sin_su_frontmatter(tmp_path: Path) -> None:
    raiz = tmp_path / "repo"
    shutil.copytree(RAIZ / "lecciones", raiz / "lecciones", ignore=shutil.ignore_patterns("*.qmd"))
    for carpeta in ("posts", "casos"):
        if (RAIZ / carpeta).is_dir():
            shutil.copytree(RAIZ / carpeta, raiz / carpeta)
    shutil.copyfile(RAIZ / "CITATION.cff", raiz / "CITATION.cff")
    (raiz / "lecciones" / "paratextos" / "autores.md").write_text(_completo(), encoding="utf-8")
    dedicatoria = raiz / "lecciones" / "paratextos" / "dedicatoria.md"
    dedicatoria.write_text(
        dedicatoria.read_text(encoding="utf-8")
        .replace("estado: propuesta", "estado: aprobada")
        .replace("aprobada_por: []", f"aprobada_por: [{', '.join(VIVOS)}]")
        .replace("fecha: null", f"fecha: {FECHA}"),
        encoding="utf-8",
    )
    salida = tmp_path / "quarto"
    generar_proyecto_quarto(salida, raiz)
    qmd = (salida / "P-autores.qmd").read_text(encoding="utf-8")
    assert "aprobada_por" not in qmd
    assert qmd.lstrip().startswith("## SOBRE LOS AUTORES")
    assert "### Daniela Torres Tobar {#sobre-dtt .unnumbered}" in qmd
    assert "Daniela Torres Tobar es una persona de prueba." in qmd
