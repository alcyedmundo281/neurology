"""Primera edición (ADR-001, D6) y temas de los capítulos excluidos (D7)."""

from __future__ import annotations

import pytest

from lecciones import mapa as m
from lecciones.fuente import RAIZ
from libro.datos import leer_metadatos
from libro.qmd import _datos_libro_tex, edicion_texto


def test_la_obra_es_primera_edicion() -> None:
    meta = leer_metadatos(RAIZ)
    assert meta.edicion == 1
    assert edicion_texto(meta) == "Primera edición"
    tex = _datos_libro_tex(meta)
    assert "PRIMERA EDICIÓN" in tex and "Primera edición" in tex


@pytest.mark.parametrize(
    "ruta", ["tools/libro/qmd.py", "assets/libro/preambulo.tex", ".zenodo.json", "README.md"]
)
def test_ninguna_salida_presenta_la_obra_como_continuacion_de_otra_edicion(ruta: str) -> None:
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    for frase in ("Nueva edición", "NUEVA EDICIÓN", "continúa la obra", "Continúa", "2.ª ed. (UCE"):
        assert frase not in texto, f"{ruta}: «{frase}»"


@pytest.mark.parametrize(
    ("ident", "titulo"),
    [
        ("leccion-otras-drogas-antiepilepticas", "Otras drogas antiepilépticas"),
        ("leccion-trastornos-movimiento-nino", "Los trastornos del movimiento"),
    ],
)
def test_los_temas_excluidos_siguen_en_el_mapa_sin_legado(ident: str, titulo: str) -> None:
    fila = m.cargar().fila(ident)
    assert fila is not None
    assert fila.titulo == titulo
    assert fila.parte == "lactante-nino"
    assert fila.legado_paginas is None
