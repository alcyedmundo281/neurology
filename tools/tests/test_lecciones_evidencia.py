"""Evidencia de las lecciones a una revisión fijada: posts/ + lecciones/evidencia/ (ADR-001)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import yaml

from casos.errores import ErrorDeCaso
from lecciones.evidencia import cargar_articulos
from lecciones.fuente import RAIZ
from lecciones.tokens import ErrorDeToken, resolver_texto

if TYPE_CHECKING:
    from pathlib import Path

REV_A = "a" * 40
REV_B = "b" * 40


def escribir(carpeta: Path, condicion: str, revision: str, item: dict[str, Any]) -> None:
    """Un artículo mínimo, con el formato que escribe generate_topic.py."""
    carpeta.mkdir(parents=True, exist_ok=True)
    cabecera = {
        "slug": f"tema-{condicion.lower().replace(':', '')}",
        "date": "2026-11-01",
        "grounding": {"condicion_id": condicion, "condicion_nombre": condicion},
        "fuente": {"revision": revision},
        "evidencia": [{"concepto": "HM:3240", **item}],
    }
    cuerpo = "### Fontanela anterior abombada (HM:3240)\n"
    texto = "---\n" + yaml.safe_dump(cabecera, allow_unicode=True) + "---\n" + cuerpo
    (carpeta / f"{condicion.replace(':', '')}.md").write_text(texto, encoding="utf-8")


MEDIDO: dict[str, Any] = {
    "estado_lr": "medido",
    "lr_positivo": {"valor": 3.5, "ic95": [2.0, 6.0]},
    "sensibilidad": 0.5,
}
NO_MEDIDO: dict[str, Any] = {"estado_lr": "no_medido", "sensibilidad": 0.95}


# --- lectura de una única revisión -----------------------------------------------------------


def test_las_lecciones_leen_los_articulos_publicados_y_los_reservados(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6004", REV_A, MEDIDO)
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_A, NO_MEDIDO)
    assert sorted(cargar_articulos(tmp_path)) == ["HM:6004", "HM:6049"]


def test_una_condicion_reservada_se_cita_aunque_no_se_publique(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6004", REV_A, MEDIDO)
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_A, NO_MEDIDO)
    declaradas = ["HM:6004", "HM:6049"]
    texto = resolver_texto("{{sens HM:3240>HM:6049}}", declaradas, cargar_articulos(tmp_path))
    assert texto == "sensibilidad 0.95"


def test_revisiones_distintas_son_un_error(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6004", REV_A, MEDIDO)
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_B, NO_MEDIDO)
    with pytest.raises(ErrorDeCaso, match="varias revisiones"):
        cargar_articulos(tmp_path)


def test_condicion_publicada_y_reservada_a_la_vez_es_un_error(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6049", REV_A, MEDIDO)
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_A, MEDIDO)
    with pytest.raises(ErrorDeCaso, match="a la vez"):
        cargar_articulos(tmp_path)


def test_sin_carpetas_no_hay_evidencia(tmp_path: Path) -> None:
    assert cargar_articulos(tmp_path) == {}


# --- los tres fallos que la exclusión del blog no puede relajar ---------------------------------


def test_falla_si_el_concepto_no_existe_en_esa_revision(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6004", REV_A, MEDIDO)
    with pytest.raises(ErrorDeToken, match="ninguna condición declarada"):
        resolver_texto("{{lr+ HM:9999}}", ["HM:6004"], cargar_articulos(tmp_path))


def test_falla_si_el_token_es_ambiguo_aunque_una_condicion_sea_reservada(tmp_path: Path) -> None:
    escribir(tmp_path / "posts", "HM:6004", REV_A, MEDIDO)
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_A, MEDIDO)
    with pytest.raises(ErrorDeToken, match="nombre la condición"):
        resolver_texto("{{lr+ HM:3240}}", ["HM:6004", "HM:6049"], cargar_articulos(tmp_path))


def test_falla_si_la_arista_no_tiene_la_metrica_pedida(tmp_path: Path) -> None:
    sin_especificidad = {"estado_lr": "no_medido", "sensibilidad": 0.95}
    escribir(tmp_path / "lecciones" / "evidencia", "HM:6049", REV_A, sin_especificidad)
    articulos = cargar_articulos(tmp_path)
    with pytest.raises(ErrorDeToken, match="no registra especificidad"):
        resolver_texto("{{esp HM:3240}}", ["HM:6049"], articulos)
    with pytest.raises(ErrorDeToken, match="no hay LR medido"):
        resolver_texto("{{lr+ HM:3240}}", ["HM:6049"], articulos)


# --- el repositorio real ----------------------------------------------------------------------


def test_el_repositorio_lee_una_sola_revision_y_cita_hm6049() -> None:
    articulos = cargar_articulos(RAIZ)
    assert {"HM:6004", "HM:6049"} <= set(articulos)
    assert len({a.revision_fuente for a in articulos.values()}) == 1
    # La exclusión del blog no quita la evidencia de las lecciones.
    assert not (RAIZ / "posts" / "HM6049-paralisis-cerebral.md").exists()
    assert (RAIZ / "lecciones" / "evidencia" / "HM6049-paralisis-cerebral.md").is_file()
