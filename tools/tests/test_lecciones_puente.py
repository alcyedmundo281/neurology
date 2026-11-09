"""Puente lecciones → blog y libro: tokens con condición explícita y proyección (ADR-001)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from casos.articulo import Articulo
from lecciones.fuente import Archivo
from lecciones.modelo import Leccion
from lecciones.proyectar import (
    lecciones_por_parte,
    problemas_de_resolucion,
    proyectar,
)
from lecciones.tokens import TOKEN, ErrorDeToken, problemas_de_tokens, resolver_texto
from lecciones.validacion import problemas_de_evidencia
from libro.datos import RAIZ, leer_metadatos
from libro.qmd import _configuracion_quarto


def articulo(condicion: str, lr: float, ic: list[float]) -> Articulo:
    return Articulo(
        ruta=Path(f"posts/{condicion}.md"),
        condicion_id=condicion,
        condicion_nombre=condicion,
        slug=condicion.lower(),
        fecha="2026-11-01",
        revision_fuente="abc1234",
        concepto_principal=None,
        evidencia={
            "HM:3240": [
                {
                    "concepto": "HM:3240",
                    "estado_lr": "medido",
                    "lr_positivo": {"valor": lr, "ic95": ic},
                    "sensibilidad": 0.5,
                }
            ]
        },
        nombres={"HM:3240": "Fontanela anterior abombada"},
        referencias={},
    )


A = articulo("HM:6004", 3.5, [2.0, 6.0])
B = articulo("HM:6049", 1.2, [1.0, 1.5])
SOLO_A = {"HM:6004": A}
AMBAS = {"HM:6004": A, "HM:6049": B}
DECLARADAS = ["HM:6004", "HM:6049"]


# --- sintaxis ------------------------------------------------------------------------------


def test_el_token_admite_condicion_medicion_y_tramo() -> None:
    m = TOKEN.fullmatch("{{lr+ HM:3240>HM:6004@2#1}}")
    assert m is not None
    assert (m["tipo"], m["id"], m["cond"], m["n"], m["t"]) == (
        "lr+",
        "HM:3240",
        "HM:6004",
        "2",
        "1",
    )
    sin = TOKEN.fullmatch("{{sens HM:3240}}")
    assert sin is not None
    assert sin["cond"] is None


# --- resolución ----------------------------------------------------------------------------


def test_concepto_en_una_sola_condicion_resuelve_contra_ella() -> None:
    texto = resolver_texto("Tiene {{lr+ HM:3240}}.", DECLARADAS, SOLO_A)
    assert texto == "Tiene LR+ 3.5 (IC 95 %: 2.0–6.0)."


def test_concepto_en_varias_condiciones_exige_la_condicion() -> None:
    with pytest.raises(ErrorDeToken, match=r"nombre la condición.*HM:3240>HM:6004"):
        resolver_texto("{{lr+ HM:3240}}", DECLARADAS, AMBAS)


def test_con_la_condicion_explicita_resuelve_cada_arista() -> None:
    a = resolver_texto("{{lr+ HM:3240>HM:6004}}", DECLARADAS, AMBAS)
    b = resolver_texto("{{lr+ HM:3240>HM:6049}}", DECLARADAS, AMBAS)
    assert "3.5" in a
    assert "1.2" in b


def test_condicion_no_declarada_por_la_leccion_falla() -> None:
    with pytest.raises(ErrorDeToken, match="no declara esa condición"):
        resolver_texto("{{lr+ HM:3240>HM:6049}}", ["HM:6004"], AMBAS)


def test_condicion_sin_el_concepto_falla() -> None:
    sin = articulo("HM:6049", 1.0, [1.0, 2.0])
    sin.evidencia.clear()
    with pytest.raises(ErrorDeToken, match="no está en la evidencia de HM:6049"):
        resolver_texto("{{lr+ HM:3240>HM:6049}}", DECLARADAS, {"HM:6049": sin})


def test_condicion_declarada_sin_articulo_falla() -> None:
    with pytest.raises(ErrorDeToken, match="sin artículo en posts/ ni en lecciones/evidencia/"):
        resolver_texto("{{lr+ HM:3240>HM:6049}}", DECLARADAS, SOLO_A)


def test_token_sin_resolver_nunca_queda_como_texto_crudo() -> None:
    with pytest.raises(ErrorDeToken, match="ninguna condición declarada"):
        resolver_texto("Antes {{lr+ HM:9999}} después", DECLARADAS, AMBAS)


def test_se_informan_todos_los_tokens_rotos() -> None:
    texto = "{{lr+ HM:9999}} y {{sens HM:8888}} y {{lr+ HM:3240>HM:6004}}"
    problemas = problemas_de_tokens(texto, DECLARADAS, AMBAS)
    assert len(problemas) == 2


def test_lr_no_medido_no_se_cita() -> None:
    nm = articulo("HM:6004", 3.5, [2.0, 6.0])
    nm.evidencia["HM:3240"][0]["estado_lr"] = "no_medido"
    with pytest.raises(ErrorDeToken, match="no hay LR medido"):
        resolver_texto("{{lr+ HM:3240}}", DECLARADAS, {"HM:6004": nm})


# --- contrato de la lección ----------------------------------------------------------------


def _leccion_base(**cambios: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "leccion-prueba",
        "tipo": "leccion",
        "titulo": "Lección de prueba",
        "parte": "neonato",
        "orden": 1,
        "estado": "borrador",
        "autores": [
            {
                "nombre": "Alcy Ramiro Torres Guerrero",
                "orcid": "0000-0002-9742-375X",
                "credit": ["redaccion", "revision-edicion"],
            }
        ],
        "uso_ia": [],
        "pregunta_clinica": "¿Qué dice la fontanela?",
        "abstract": " ".join(["palabra"] * 50),
        "dialogo_clinico": "Un niño con la fontanela abombada.",
        "indispensable": ["Una perla."],
        "limites": ["Un límite."],
        "condiciones": DECLARADAS,
        "conceptos": ["HM:3240"],
        "refs": [],
    }
    return {**base, **cambios}


def test_la_condicion_del_token_debe_estar_declarada() -> None:
    leccion = Leccion.model_validate(_leccion_base(condiciones=["HM:6004"]))
    problemas = problemas_de_evidencia("{{lr+ HM:3240>HM:6049}}", leccion)
    assert any("no figura en «condiciones»" in p for p in problemas)


def test_el_concepto_del_token_con_condicion_sigue_declarado() -> None:
    leccion = Leccion.model_validate(_leccion_base(conceptos=[]))
    problemas = problemas_de_evidencia("{{lr+ HM:3240>HM:6004}}", leccion)
    assert any("no figura en «conceptos»" in p for p in problemas)


def _archivo(cuerpo: str, **cambios: Any) -> Archivo:
    return Archivo(ruta=Path("leccion-prueba.qmd"), datos=_leccion_base(**cambios), cuerpo=cuerpo)


def test_check_marca_condicion_sin_articulo_y_token_roto() -> None:
    archivo = _archivo("## Qué significa\n\nTiene {{lr+ HM:3240}}.\n")
    problemas = problemas_de_resolucion(archivo, SOLO_A)
    assert any("HM:6049 declarada pero sin artículo" in p for p in problemas)
    assert not any("HM:3240" in p for p in problemas)  # resuelve contra HM:6004


def test_check_revisa_tambien_los_campos_del_frontmatter() -> None:
    archivo = _archivo("## Qué significa\n\nTexto.\n", abstract="Dice {{lr+ HM:9999}}.")
    problemas = problemas_de_resolucion(archivo, AMBAS)
    assert any("HM:9999" in p for p in problemas)


def test_el_check_ignora_tokens_dentro_de_codigo() -> None:
    archivo = _archivo("## Qué significa\n\nSintaxis: `{{lr+ HM:9999}}`.\n")
    assert problemas_de_resolucion(archivo, AMBAS) == []


# --- proyección ----------------------------------------------------------------------------


def test_proyeccion_de_capitulo_resuelve_y_no_deja_llaves() -> None:
    archivo = _archivo("## Qué significa\n\nTiene {{lr+ HM:3240>HM:6004}}.\n")
    texto = proyectar(archivo, AMBAS, "capitulo")
    assert texto.startswith("# Lección de prueba {#sec-leccion-prueba}")
    assert "LR+ 3.5 (IC 95 %: 2.0–6.0)" in texto
    assert "{{" not in texto
    assert "## Dónde no confiar" in texto
    assert "{.perlas-clinicas}" in texto
    assert "{.caso-socratico}" in texto


def test_proyeccion_autonoma_lleva_bibliografia_en_el_frontmatter() -> None:
    texto = proyectar(_archivo("## Qué significa\n\nTexto.\n"), AMBAS, "autonomo")
    assert texto.startswith("---\n")
    assert "bibliography: refs.bib" in texto
    assert "title: Lección de prueba" in texto


def test_proyeccion_aborta_si_un_token_no_resuelve() -> None:
    archivo = _archivo("## Qué significa\n\n{{lr+ HM:9999}}\n")
    with pytest.raises(ErrorDeToken):
        proyectar(archivo, AMBAS, "capitulo")


# --- libro ---------------------------------------------------------------------------------


def test_el_libro_incluye_las_lecciones_por_parte_del_mapa() -> None:
    partes = lecciones_por_parte(RAIZ, incluir_borradores=True)
    titulos = [t for t, _ in partes]
    assert "El recién nacido" in titulos
    assert any(r.stem == "leccion-examen-neurologico-recien-nacido" for _, rs in partes for r in rs)


def test_la_configuracion_del_libro_no_cambia_sin_lecciones() -> None:
    meta = leer_metadatos(RAIZ)
    sin = _configuracion_quarto(meta, ["a.qmd"])
    assert "bibliography" not in sin
    assert sin["book"]["chapters"] == ["index.qmd", "a.qmd"]  # type: ignore[index]
    parte = {"part": "El recién nacido", "chapters": ["l.qmd"]}
    con = _configuracion_quarto(meta, [parte], con_bibliografia=True)
    assert con["bibliography"] == "refs.bib"
    assert con["book"]["chapters"] == ["index.qmd", parte]  # type: ignore[index]
