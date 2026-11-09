"""Revisión del puente: borradores fuera del libro, texto escaneado único y mensajes (ADR-001)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from casos.articulo import Articulo
from lecciones.fuente import RAIZ, Archivo
from lecciones.proyectar import (
    AVISO_BORRADOR,
    lecciones_por_parte,
    problemas_de_resolucion,
    proyectar,
)
from lecciones.tokens import ErrorDeToken, resolver_texto
from libro.qmd import generar_proyecto_quarto

MEDIDO: dict[str, Any] = {
    "estado_lr": "medido",
    "lr_positivo": {"valor": 3.5, "ic95": [2.0, 6.0]},
}


def articulo(condicion: str = "HM:6004") -> Articulo:
    return Articulo(
        ruta=Path("posts/x.md"),
        condicion_id=condicion,
        condicion_nombre=condicion,
        slug="x",
        fecha="2026-11-01",
        revision_fuente="abc1234",
        concepto_principal=None,
        evidencia={"HM:3240": [{"concepto": "HM:3240", **MEDIDO}]},
        nombres={"HM:3240": "Fontanela anterior abombada"},
        referencias={},
    )


ARTICULOS = {"HM:6004": articulo()}


def archivo(cuerpo: str, **cambios: Any) -> Archivo:
    datos: dict[str, Any] = {
        "id": "leccion-prueba",
        "titulo": "Lección de prueba",
        "estado": "borrador",
        "abstract": "Resumen.",
        "dialogo_clinico": "Diálogo.",
        "indispensable": ["Una perla."],
        "limites": ["Un límite."],
        "condiciones": ["HM:6004"],
        **cambios,
    }
    return Archivo(ruta=Path("leccion-prueba.qmd"), datos=datos, cuerpo=cuerpo)


# --- 1. borradores fuera del libro ----------------------------------------------------------


def _raiz_con_lecciones(tmp_path: Path, estados: dict[str, str]) -> Path:
    carpeta = tmp_path / "lecciones"
    carpeta.mkdir()
    shutil.copyfile(RAIZ / "lecciones" / "mapa.yaml", carpeta / "mapa.yaml")
    for orden, (ident, estado) in enumerate(estados.items(), 1):
        cabecera = {"id": ident, "parte": "neonato", "orden": orden, "estado": estado}
        texto = "---\n" + yaml.safe_dump(cabecera) + "---\n## Cómo se explora\n\nTexto.\n"
        (carpeta / f"{ident}.qmd").write_text(texto, encoding="utf-8")
    return tmp_path


def test_por_defecto_solo_entran_lecciones_revisadas_o_publicadas(tmp_path: Path) -> None:
    raiz = _raiz_con_lecciones(
        tmp_path,
        {
            "leccion-a-borrador": "borrador",
            "leccion-b-revisada": "revisado",
            "leccion-c-publicada": "publicado",
        },
    )
    partes = lecciones_por_parte(raiz)
    assert [r.stem for _, rutas in partes for r in rutas] == [
        "leccion-b-revisada",
        "leccion-c-publicada",
    ]


def test_incluir_borradores_las_añade_en_su_orden(tmp_path: Path) -> None:
    raiz = _raiz_con_lecciones(
        tmp_path, {"leccion-a-borrador": "borrador", "leccion-b-revisada": "revisado"}
    )
    partes = lecciones_por_parte(raiz, incluir_borradores=True)
    assert [r.stem for _, rutas in partes for r in rutas] == [
        "leccion-a-borrador",
        "leccion-b-revisada",
    ]


def test_sin_lecciones_publicables_no_hay_parte(tmp_path: Path) -> None:
    raiz = _raiz_con_lecciones(tmp_path, {"leccion-a-borrador": "borrador"})
    assert lecciones_por_parte(raiz) == []


def test_un_borrador_lleva_su_aviso_visible() -> None:
    texto = proyectar(archivo("## Qué significa\n\nTexto.\n"), ARTICULOS, "capitulo")
    assert "Borrador — sin revisión humana" in texto
    assert AVISO_BORRADOR in texto
    assert texto.index(AVISO_BORRADOR) < texto.index("## Qué significa")


@pytest.mark.parametrize("estado", ["revisado", "publicado"])
def test_una_leccion_revisada_no_lleva_aviso(estado: str) -> None:
    texto = proyectar(archivo("## Qué significa\n\nTexto.\n", estado=estado), ARTICULOS)
    assert "Borrador" not in texto


def test_el_libro_excluye_los_borradores_salvo_vista_previa(tmp_path: Path) -> None:
    sin = tmp_path / "sin"
    generar_proyecto_quarto(sin, RAIZ, exigir_semblanzas=False)
    assert not list(sin.glob("L-*.qmd"))
    assert "bibliography" not in (sin / "_quarto.yml").read_text(encoding="utf-8")

    con = tmp_path / "con"
    generar_proyecto_quarto(con, RAIZ, incluir_borradores=True, exigir_semblanzas=False)
    capitulos = list(con.glob("L-*.qmd"))
    assert capitulos
    for capitulo in capitulos:
        assert "Borrador — sin revisión humana" in capitulo.read_text(encoding="utf-8")


def test_el_libro_avisa_si_no_hay_lecciones_publicables(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    assert "--incluir-borradores" in capsys.readouterr().err


# --- 2. un único texto escaneado ------------------------------------------------------------

CUERPO_CON_TOKENS_PROTEGIDOS = (
    "## Qué significa\n\n"
    "Real: {{lr+ HM:3240}}.\n\n"
    "En código: `{{lr+ HM:9999}}`.\n\n"
    "<!-- comentario con {{lr+ HM:9998}} -->\n\n"
    "```\n{{lr+ HM:9997}}\n```\n"
)


def test_un_token_en_codigo_o_comentario_ni_se_comprueba_ni_se_resuelve() -> None:
    leccion = archivo(CUERPO_CON_TOKENS_PROTEGIDOS)
    assert problemas_de_resolucion(leccion, ARTICULOS) == []
    texto = proyectar(leccion, ARTICULOS, "capitulo")
    assert "LR+ 3.5" in texto  # el token real sí
    for crudo in ("{{lr+ HM:9999}}", "{{lr+ HM:9998}}", "{{lr+ HM:9997}}"):
        assert crudo in texto  # los protegidos quedan tal cual


def test_el_token_real_roto_sigue_fallando_aunque_haya_protegidos() -> None:
    leccion = archivo("## Qué significa\n\n{{lr+ HM:9996}} y `{{lr+ HM:9999}}`.\n")
    assert len(problemas_de_resolucion(leccion, ARTICULOS)) == 1
    with pytest.raises(ErrorDeToken):
        proyectar(leccion, ARTICULOS)


def test_comprobacion_y_proyeccion_coinciden_en_lo_escaneable() -> None:
    from lecciones.validacion import CENTINELA, _limpio, proteger

    protegido, guardados = proteger(CUERPO_CON_TOKENS_PROTEGIDOS)
    assert CENTINELA.sub("", protegido) == _limpio(CUERPO_CON_TOKENS_PROTEGIDOS)
    assert len(guardados) == 3


# --- 3. mensajes de error -------------------------------------------------------------------


def test_los_mensajes_nombran_los_dos_origenes() -> None:
    leccion = archivo("## Qué significa\n\nTexto.\n", condiciones=["HM:6004", "HM:6049"])
    problemas = problemas_de_resolucion(leccion, ARTICULOS)
    assert any("sin artículo en posts/ ni en lecciones/evidencia/" in p for p in problemas)
    with pytest.raises(ErrorDeToken, match="sin artículo en posts/ ni en lecciones/evidencia/"):
        resolver_texto("{{lr+ HM:3240>HM:6049}}", ["HM:6004", "HM:6049"], ARTICULOS)
