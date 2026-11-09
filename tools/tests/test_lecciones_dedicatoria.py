"""Dedicatoria: texto exacto, fechas del mapa y aprobación de los autores vivos."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from lecciones import dedicatoria as d
from lecciones.mapa import cargar as cargar_mapa
from libro.datos import RAIZ
from libro.qmd import generar_proyecto_quarto

if TYPE_CHECKING:
    from pathlib import Path

MAPA = cargar_mapa(RAIZ / "lecciones" / "mapa.yaml")
RUTA = RAIZ.joinpath(*d.RUTA)
VIVOS = ["artg", "gtg", "aetg", "dtt"]
IMPRESA = (
    "A nuestro padre y abuelo,\n"
    "Alcy Torres Catefort (1937–2022).\n"
    "«No debe hacerse de prisa».\n"
    "Así enseñó a examinar a un niño,\n"
    "y así hemos querido rehacer su libro."
)


def _aprobada(texto: str) -> str:
    return texto.replace("estado: propuesta", "estado: aprobada").replace(
        "aprobada_por: []\nfecha: null", f"aprobada_por: [{', '.join(VIVOS)}]\nfecha: 2026-11-03"
    )


def test_las_fechas_de_atc_salen_del_mapa() -> None:
    atc = MAPA.personas["atc"]
    assert (atc.nacimiento.isoformat(), atc.fallecimiento.isoformat()) == (  # type: ignore[union-attr]
        "1937-12-19",
        "2022-01-09",
    )


def test_el_texto_impreso_es_exacto() -> None:
    impreso = d.renderizar(RUTA.read_text(encoding="utf-8"), MAPA)
    lineas = [ln.rstrip() for ln in impreso.strip().splitlines()]
    assert "\n".join(lineas) == IMPRESA


def test_no_lleva_titulo_ni_frontmatter() -> None:
    impreso = d.renderizar(RUTA.read_text(encoding="utf-8"), MAPA)
    assert "#" not in impreso
    assert "estado" not in impreso
    assert "{vida" not in impreso


def test_la_dedicatoria_del_repositorio_es_una_propuesta() -> None:
    problemas = d.verificar(RAIZ)
    assert problemas == ["dedicatoria: propuesta, sin aprobar por los autores vivos"]


def test_aprobada_por_los_autores_vivos_se_puede_imprimir() -> None:
    texto = _aprobada(RUTA.read_text(encoding="utf-8"))
    assert d.problemas_de_dedicatoria(texto, MAPA) == []


@pytest.mark.parametrize("falta", VIVOS)
def test_cada_autor_vivo_debe_aprobar(falta: str) -> None:
    texto = (
        _aprobada(RUTA.read_text(encoding="utf-8"))
        .replace(falta + ", ", "")
        .replace(", " + falta + "]", "]")
    )
    problemas = d.problemas_de_dedicatoria(texto, MAPA)
    assert len(problemas) == 1
    assert MAPA.personas[falta].nombre in problemas[0]


def test_aprobar_sin_fecha_no_basta() -> None:
    texto = _aprobada(RUTA.read_text(encoding="utf-8")).replace("fecha: 2026-11-03", "fecha: null")
    assert d.problemas_de_dedicatoria(texto, MAPA) == ["dedicatoria: falta la fecha de aprobación"]


def test_las_fechas_no_se_escriben_a_mano() -> None:
    texto = RUTA.read_text(encoding="utf-8").replace("{vida:atc}", "1937–2022")
    problemas = d.problemas_de_dedicatoria(_aprobada(texto), MAPA)
    assert any("no escriba las fechas a mano" in p for p in problemas)


def test_la_compilacion_falla_mientras_sea_propuesta(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="La dedicatoria no está lista"):
        generar_proyecto_quarto(tmp_path / "libro", RAIZ)


def test_aprobada_la_dedicatoria_va_tras_los_creditos_y_no_al_final(tmp_path: Path) -> None:
    raiz = tmp_path / "repo"
    for ruta in (
        "lecciones/mapa.yaml",
        "lecciones/paratextos/declaracion-ia.md",
        "lecciones/AI-USE.md",
        "CITATION.cff",
    ):
        destino = raiz / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes((RAIZ / ruta).read_bytes())
    (raiz / "lecciones" / "paratextos" / "dedicatoria.md").write_text(
        _aprobada(RUTA.read_text(encoding="utf-8")), encoding="utf-8"
    )
    (raiz / "lecciones" / "paratextos" / "autores.md").write_bytes(
        (RAIZ / "lecciones" / "paratextos" / "autores.md").read_bytes()
    )
    generar_proyecto_quarto(tmp_path / "libro", raiz, exigir_semblanzas=False)
    index = (tmp_path / "libro" / "index.qmd").read_text(encoding="utf-8")
    assert index.index("{.creditos-pdf}") < index.index("{.dedicatoria-pdf}")
    assert index.index("{.dedicatoria-pdf}") < index.index("tableofcontents")
    assert "Alcy Torres Catefort (1937–2022)." in index
    assert not (tmp_path / "libro" / "P-dedicatoria.qmd").exists()
