"""Revisión de las partes y firma bibliográfica (ADR-001): el editor revisa todo."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from casos.articulo import Articulo
from lecciones import mapa as m
from lecciones.fuente import Archivo
from lecciones.modelo import Autor, Leccion
from lecciones.proyectar import linea_revision, proyectar

FIRMAS = {
    "Alcy Ramiro Torres Guerrero": "Alcy R. Torres",
    "Alcy Edmundo Torres Guerrero": "Alcy Edmundo Torres Guerrero",
}


def test_el_editor_revisa_todas_las_partes() -> None:
    mapa = m.cargar()
    assert {p.revisor for p in mapa.partes} == {"aetg"}


def test_el_especialista_es_autor_de_su_area() -> None:
    mapa = m.cargar()
    assert mapa.parte("neonato").autores == ["atc", "artg"]
    assert mapa.parte("lactante-nino").autores == ["atc", "artg"]
    assert mapa.parte("neuroftalmologia").autores == ["gtg"]


def test_dtt_escribe_las_autoevaluaciones_y_las_revisa_el_editor() -> None:
    mapa = m.cargar()
    dtt = mapa.personas["dtt"]
    assert dtt.nombre == "Daniela Torres Tobar"
    assert dtt.orcid is None
    assert dtt.credit == ["redaccion", "curacion-de-datos"]
    assert list(mapa.personas)[-1] == "dtt"
    assert mapa.autoevaluaciones is not None
    assert mapa.autoevaluaciones.autores == ["dtt"]
    assert mapa.autoevaluaciones.revisor == "aetg"
    # No es autora de ninguna parte: las lecciones no la llevan en su frontmatter.
    assert all("dtt" not in p.autores for p in mapa.partes)


def test_no_hay_corevisores() -> None:
    assert "corevisor" not in m.FilaMapa.model_fields
    assert "corevisor" not in Leccion.model_fields
    assert "corevisor:" not in m.MAPA.read_text(encoding="utf-8")


def test_artg_firma_como_alcy_r_torres_pero_la_portada_usa_el_nombre_completo() -> None:
    mapa = m.cargar()
    artg = mapa.personas["artg"]
    assert artg.nombre == "Alcy Ramiro Torres Guerrero"
    assert artg.nombre_bibliografico == "Alcy R. Torres"
    assert mapa.personas["aetg"].nombre_bibliografico == "Alcy E. Torres-Guerrero"
    assert mapa.personas["gtg"].nombre_bibliografico == "Gladys Torres-Guerrero"
    assert mapa.personas["atc"].nombre_bibliografico is None


def test_la_firma_bibliografica_es_opcional() -> None:
    assert (
        Autor.model_validate({"nombre": "Alguien", "credit": ["redaccion"]}).nombre_bibliografico
        is None
    )


def test_la_linea_de_revision_usa_la_firma_bibliografica() -> None:
    datos = {
        "estado": "revisado",
        "revisor": "Alcy Ramiro Torres Guerrero",
        "fecha_revision": date(2026, 11, 2),
    }
    assert linea_revision(datos, FIRMAS) == "*Revisión clínica: Alcy R. Torres (2026-11-02)*"


def test_un_borrador_no_lleva_linea_de_revision() -> None:
    assert linea_revision({"estado": "borrador", "revisor": "x"}, FIRMAS) is None


def test_la_proyeccion_de_una_leccion_revisada_lleva_la_linea() -> None:
    articulo = Articulo(
        ruta=Path("posts/x.md"),
        condicion_id="HM:6004",
        condicion_nombre="x",
        slug="x",
        fecha="2026-11-01",
        revision_fuente="abc1234",
        concepto_principal=None,
        evidencia={},
        nombres={},
        referencias={},
    )
    datos = {
        "id": "leccion-prueba",
        "titulo": "Lección de prueba",
        "estado": "revisado",
        "revisor": "Alcy Ramiro Torres Guerrero",
        "fecha_revision": date(2026, 11, 2),
        "abstract": "Resumen.",
        "dialogo_clinico": "Diálogo.",
        "indispensable": ["Una perla."],
        "limites": ["Un límite."],
        "condiciones": [],
    }
    archivo = Archivo(Path("leccion-prueba.qmd"), datos, "## Qué significa\n\nTexto.\n")
    texto = proyectar(archivo, {"HM:6004": articulo}, firmas=FIRMAS)
    assert "Revisión clínica: Alcy R. Torres (2026-11-02)" in texto
    assert "Borrador" not in texto


@pytest.mark.parametrize("campo", ["corevisor", "fecha_corevision"])
def test_una_leccion_no_acepta_campos_de_corevision(campo: str) -> None:
    with pytest.raises(ValueError, match=campo):
        Leccion.model_validate({"id": "leccion-prueba", campo: "x"})
