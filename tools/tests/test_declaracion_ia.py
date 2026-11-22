"""La declaración de uso de IA del libro, como en biosemiotics: al frente, describiendo la edición,
y declarada también en cada capítulo."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest
from lecciones.fuente import RAIZ
from lecciones.proyectar import linea_uso_ia
from lecciones.validacion import problemas_de_declaracion
from libro.qmd import _contenido_edicion, declaracion_ia, fecha_larga

if TYPE_CHECKING:
    from pathlib import Path


def test_la_edicion_cuenta_solo_lo_revisado_y_avisa_de_los_borradores() -> None:
    incluidas = [
        {"estado": "revisado", "fecha_revision": date(2026, 11, 20)},
        {"estado": "publicado", "fecha_revision": "2026-11-21"},
        {"estado": "borrador", "fecha_revision": None},
    ]
    lecciones, fecha = _contenido_edicion(incluidas)
    assert lecciones == "2 revisadas y 1 borrador sin revisión humana (vista previa)"
    assert fecha == "21 de noviembre de 2026"


def test_sin_lecciones_revisadas_no_se_inventa_una_fecha() -> None:
    assert _contenido_edicion([]) == ("ninguna revisada", "ninguna todavía")


def test_una_sola_leccion_en_singular() -> None:
    lecciones, _ = _contenido_edicion([{"estado": "revisado", "fecha_revision": "2026-11-02"}])
    assert lecciones == "una revisada"


def test_la_fecha_larga() -> None:
    assert fecha_larga(date(2026, 1, 9)) == "9 de enero de 2026"


def test_la_declaracion_del_repositorio_sustituye_sus_tres_marcadores() -> None:
    texto = declaracion_ia(RAIZ, [], 0)
    assert "{" not in texto.split("\n", 1)[1]  # el título lleva {.unnumbered}; el cuerpo, nada
    assert "las 0 citas" in " ".join(texto.split())
    assert "Lecciones de esta edición: ninguna revisada." in texto


@pytest.mark.parametrize("marcador", ["{N}", "{LECCIONES_EDICION}", "{FECHA_CORTE}"])
def test_sin_un_marcador_ni_el_check_ni_el_libro_lo_aceptan(tmp_path: Path, marcador: str) -> None:
    colofon = (RAIZ / "lecciones" / "paratextos" / "declaracion-ia.md").read_text(encoding="utf-8")
    destino = tmp_path / "lecciones" / "paratextos"
    destino.mkdir(parents=True)
    (destino / "declaracion-ia.md").write_text(colofon.replace(marcador, ""), encoding="utf-8")
    (tmp_path / "lecciones" / "AI-USE.md").write_text("## Qué ya falló\n", encoding="utf-8")
    assert any(marcador in p for p in problemas_de_declaracion(tmp_path))
    with pytest.raises(ValueError, match="exactamente una vez"):
        declaracion_ia(tmp_path, [], 0)


def test_cada_capitulo_declara_su_uso_de_ia() -> None:
    linea = linea_uso_ia(["transcripcion", "busqueda-bibliografica", "redaccion-borrador"])
    assert linea == (
        "*Uso de inteligencia artificial en esta lección: transcripción de la obra de 1993, "
        "búsqueda bibliográfica y redacción del borrador.*"
    )
    assert linea_uso_ia([]) == "*Uso de inteligencia artificial en esta lección: ninguno.*"
    with pytest.raises(ValueError, match="uso_ia"):
        linea_uso_ia(None)
