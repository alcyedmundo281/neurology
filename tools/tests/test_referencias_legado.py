"""La transcripción de referencia del legado: solo la obra de la familia, sin firmas ni terceros."""

from __future__ import annotations

import re

import pytest
import yaml

from lecciones.fuente import RAIZ

CARPETA = RAIZ / "referencias-legado" / "neurologia-pediatrica-3ed"
FICHAS = sorted(CARPETA.glob("cap-*.yaml"))
# Firmas y textos de autores ajenos a la familia que la decisión del editor deja fuera.
AJENOS = re.compile(r"Bourgeois|Darras|Volpe|Sanz Gadea|P[ée]rez Fern[áa]ndez|Noboa", re.I)
FIRMA = re.compile(r"^\s*(Por\s+(Dra?\.|[A-ZÁÉÍÓÚ])|Dra?\.\s+\S.*Torres|Basil\b|Blaise\b)", re.M)


def _ficha(ruta):  # noqa: ANN001, ANN202
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def test_hay_fichas_y_ninguna_de_los_capitulos_excluidos() -> None:
    romanos = {_ficha(r)["capitulo"]["romano"] for r in FICHAS}
    assert len(FICHAS) == 26
    assert not romanos & {"XI", "XXII"}


@pytest.mark.parametrize("ruta", FICHAS, ids=lambda r: r.stem)
def test_sin_terceros_ni_firmas_ni_preliminares(ruta) -> None:  # noqa: ANN001
    datos = _ficha(ruta)
    assert "preliminares" not in datos
    capitulo = datos["capitulo"]
    assert not AJENOS.search(capitulo["texto"])
    assert not FIRMA.search(capitulo["texto"])
    assert set(capitulo) == {
        "numero", "romano", "titulo_en_la_fuente", "autoria_distinta_del_autor_fundador",
        "citable_como_legado", "texto", "bibliografia",
    }
    assert datos["canonica"] is False


@pytest.mark.parametrize("ruta", FICHAS, ids=lambda r: r.stem)
def test_lo_que_no_es_del_autor_fundador_no_se_cita_como_legado(ruta) -> None:  # noqa: ANN001
    capitulo = _ficha(ruta)["capitulo"]
    assert capitulo["citable_como_legado"] is not capitulo["autoria_distinta_del_autor_fundador"]
