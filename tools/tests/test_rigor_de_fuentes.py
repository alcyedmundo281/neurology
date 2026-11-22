"""Auditoría de noviembre de 2026: cada agujero encontrado tiene aquí la prueba que lo cierra.

1. El revisor de una lección revisada es el que el mapa nombra para su parte.
2. Una ficha de evidencia editada a mano no coincide con medsemiotics-db en su revisión.
3. La verificación con red (citas y cifras) corre en la integración continua.
4. Las citas de 1993 llevan página dentro del rango de la lección y un cotejo humano vigente.
5. Una cifra se ancla a la cita de su oración, y la fuente citada la contiene.
6. La declaración de IA apunta a este repositorio y a sus comandos.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

import pytest
import yaml
from lecciones.cifras import TextoFuente, cotejar, numeros_de_fuente
from lecciones.fuente import RAIZ, Archivo
from lecciones.integridad import problemas_de_ficha
from lecciones.modelo import Leccion
from lecciones.validacion import problemas_de_cuerpo, problemas_de_evidencia
from pydantic import ValidationError
from tests.test_lecciones import BASE, cuerpo

from lecciones import legado
from lecciones import mapa as m

if TYPE_CHECKING:
    from pathlib import Path

HOY = date.today()


# --- 1. revisor nominado ------------------------------------------------------------------------
def _fila_revisada(revisor: str) -> dict[str, dict[str, Any]]:
    mapa = m.cargar()
    fila = mapa.fila("leccion-examen-neuroftalmologico")
    assert fila is not None
    datos = {
        "id": fila.id,
        "titulo": fila.titulo,
        "parte": fila.parte,
        "orden": fila.orden,
        "estado": "revisado",
        "revisor": revisor,
        "fecha_revision": HOY.isoformat(),
        "autores": [{"nombre": "Gladys Torres Guerrero"}],
        "_archivo": f"{fila.id}.qmd",
    }
    return {fila.id: datos}


def _errores_de_revisor(revisor: str) -> list[str]:
    return [e for e in m.coherencia(m.cargar(), _fila_revisada(revisor)) if "revisor" in e]


@pytest.mark.parametrize("revisor", ["Juan Pérez", "Gladys Torres Guerrero"])
def test_un_revisor_no_nominado_bloquea(revisor: str) -> None:
    assert _errores_de_revisor(revisor)


@pytest.mark.parametrize("revisor", ["Alcy Edmundo Torres Guerrero", "Alcy E. Torres-Guerrero"])
def test_el_revisor_nominado_pasa_con_nombre_o_firma(revisor: str) -> None:
    assert _errores_de_revisor(revisor) == []


def test_un_borrador_no_exige_revisor() -> None:
    lecciones = _fila_revisada("Juan Pérez")
    next(iter(lecciones.values()))["estado"] = "borrador"
    assert not [e for e in m.coherencia(m.cargar(), lecciones) if "revisor" in e]


def test_la_fecha_de_revision_no_puede_ser_futura() -> None:
    futura = (HOY + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError, match="futura"):
        Leccion.model_validate({**BASE, "fecha_revision": futura})


# --- 2. fichas de evidencia ---------------------------------------------------------------------
REV = "a" * 40
CONDICION = "condiciones/HM6001-prueba.yaml"
CONCEPTO = "conceptos/HM3001-signo.yaml"
SIGNOS = [{"concepto": "HM:3001", "estado_lr": "no_medido", "sensibilidad": 0.95}]


def _db() -> dict[tuple[str, str], str]:
    return {
        (REV, CONDICION): yaml.safe_dump({"id": "HM:6001", "signos": SIGNOS}),
        (REV, CONCEPTO): yaml.safe_dump({"id": "HM:3001", "tipo": "concepto", "termino": "Signo"}),
    }


def _ficha(tmp_path: Path, nombre: str = "Signo", **cambios: Any) -> Path:
    db = _db()
    datos: dict[str, Any] = {
        "slug": "prueba",
        "date": "2026-11-01",
        "fuente": {
            "revision": REV,
            "condicion": CONDICION,
            "archivos": {r: hashlib.sha256(t.encode()).hexdigest() for (_, r), t in db.items()},
        },
        "grounding": {
            "condicion_id": "HM:6001",
            "concepto_id": "HM:3001",
            "lr_positivo": None,
            "lr_negativo": None,
            "sensibilidad": 0.95,
            "especificidad": None,
        },
        "evidencia": SIGNOS,
    }
    datos.update(cambios)
    ruta = tmp_path / "HM6001-prueba.md"
    ruta.write_text(
        "---\n" + yaml.safe_dump(datos, allow_unicode=True) + f"---\n\n### {nombre} (HM:3001)\n",
        encoding="utf-8",
    )
    return ruta


def _leer(revision: str, ruta: str) -> str | None:
    return _db().get((revision, ruta))


def test_una_ficha_identica_a_la_base_pasa(tmp_path: Path) -> None:
    assert problemas_de_ficha(_ficha(tmp_path), _leer) == []


def test_una_cifra_editada_a_mano_en_la_ficha_se_detecta(tmp_path: Path) -> None:
    editada = [{**SIGNOS[0], "sensibilidad": 0.99}]
    problemas = problemas_de_ficha(_ficha(tmp_path, evidencia=editada), _leer)
    assert any("editada a mano" in p for p in problemas)


def test_un_archivo_de_la_base_con_otro_resumen_se_detecta(tmp_path: Path) -> None:
    ruta = _ficha(tmp_path)

    def leer_alterado(revision: str, r: str) -> str | None:
        texto = _leer(revision, r)
        return texto + "# cambio\n" if texto and r == CONCEPTO else texto

    assert any("SHA-256" in p for p in problemas_de_ficha(ruta, leer_alterado))


def test_una_revision_inexistente_se_detecta(tmp_path: Path) -> None:
    assert any("no existe" in p for p in problemas_de_ficha(_ficha(tmp_path), lambda r, p: None))


def test_el_nombre_del_hallazgo_debe_ser_el_de_la_base(tmp_path: Path) -> None:
    problemas = problemas_de_ficha(_ficha(tmp_path, nombre="Otro signo"), _leer)
    assert any("se llama" in p for p in problemas)


def test_el_grounding_debe_ser_el_del_signo_principal(tmp_path: Path) -> None:
    grounding = {"condicion_id": "HM:6001", "concepto_id": "HM:3001", "sensibilidad": 0.5}
    problemas = problemas_de_ficha(_ficha(tmp_path, grounding=grounding), _leer)
    assert any("grounding.sensibilidad" in p for p in problemas)


# --- 3. la verificación con red corre en CI ----------------------------------------------------
@pytest.mark.parametrize("flujo", ["ci.yml", "pages.yml"])
def test_citas_y_evidencia_corren_en_cada_flujo(flujo: str) -> None:
    texto = (RAIZ / ".github" / "workflows" / flujo).read_text(encoding="utf-8")
    assert "python -m lecciones citas" in texto
    assert "python -m lecciones evidencia" in texto
    assert "medsemiotics-db" in texto and "fetch-depth: 0" in texto


# --- 4. legado ----------------------------------------------------------------------------------
def _bloque(cita: str, atribucion: str) -> str:
    return f"::: {{.legado}}\n*«{cita}»*\n{atribucion}\n:::\n"


ATRIB = "— A. Torres Catefort, *Neurología Pediátrica*, p. 16"


def test_una_cita_fuera_de_las_paginas_de_la_leccion_bloquea() -> None:
    texto = cuerpo() + _bloque(
        "Otra cita.", "— A. Torres Catefort, *Neurología Pediátrica*, p. 412"
    )
    problemas = problemas_de_cuerpo(texto, Leccion.model_validate(BASE))
    assert any("fuera de las páginas declaradas" in p for p in problemas)


@pytest.mark.parametrize(
    "atribucion", ["— p. 16", "— A. Torres Catefort, *Neurología Pediátrica*, pp. 16"]
)
def test_la_atribucion_tiene_forma_fija(atribucion: str) -> None:
    _, problemas = legado.citas(_bloque("Cita.", atribucion))
    assert problemas


def test_el_resumen_ignora_los_saltos_de_linea_pero_no_las_palabras() -> None:
    assert legado.resumen("No debe hacerse\nde prisa.") == legado.resumen(
        "No debe hacerse de prisa."
    )
    assert legado.resumen("Debe hacerse de prisa.") != legado.resumen("No debe hacerse de prisa.")


def _registro(sha: str, por: str = "Alcy Edmundo Torres Guerrero") -> legado.Registro:
    return legado.Registro.model_validate(
        {
            "cotejos": [
                {
                    "leccion": "leccion-prueba",
                    "paginas": "16",
                    "sha256": sha,
                    "cotejado_por": por,
                    "fecha": HOY.isoformat(),
                }
            ]
        }
    )


VIVAS = {"Alcy Edmundo Torres Guerrero", "Alcy Ramiro Torres Guerrero"}


def test_una_cita_sin_cotejo_se_informa() -> None:
    citas, _ = legado.citas(_bloque("Cita.", ATRIB))
    assert legado.problemas_de_cotejo("leccion-prueba", citas, legado.Registro(), VIVAS)


def test_una_cita_cotejada_pasa_y_si_cambia_queda_huerfana() -> None:
    citas, _ = legado.citas(_bloque("Cita original.", ATRIB))
    registro = _registro(citas[0].sha)
    assert legado.problemas_de_cotejo("leccion-prueba", citas, registro, VIVAS) == []
    alterada, _ = legado.citas(_bloque("Cita alterada.", ATRIB))
    assert legado.problemas_de_cotejo("leccion-prueba", alterada, registro, VIVAS)
    assert legado.huerfanos(registro, {"leccion-prueba": {alterada[0].sha}})


@pytest.mark.parametrize("por", ["Claude", "Alcy Torres Catefort", "Juan Pérez"])
def test_coteja_una_persona_viva_del_mapa(por: str) -> None:
    citas, _ = legado.citas(_bloque("Cita.", ATRIB))
    problemas = legado.problemas_de_cotejo(
        "leccion-prueba", citas, _registro(citas[0].sha, por), VIVAS
    )
    assert any("persona viva" in p for p in problemas)


def test_el_registro_real_es_legible() -> None:
    legado.cargar_registro()


# --- 5. cifras ancladas -------------------------------------------------------------------------
def test_la_cita_del_parrafo_no_sostiene_una_cifra_de_otra_oracion() -> None:
    leccion = Leccion.model_validate({**BASE, "refs": ["futagi1999"]})
    texto = "Se administran 40 mg/kg en bolo. La prensión es simétrica [@futagi1999]."
    assert any("en su oración" in p for p in problemas_de_evidencia(texto, leccion))


def test_cada_item_de_lista_es_su_propia_afirmacion() -> None:
    leccion = Leccion.model_validate({**BASE, "refs": ["futagi1999"]})
    texto = "- Dar 40 mg/kg\n- Seguimiento seriado [@futagi1999]."
    assert any("en su oración" in p for p in problemas_de_evidencia(texto, leccion))


def _archivo(texto: str, estado: str = "borrador", **datos: Any) -> Archivo:
    return Archivo(ruta=RAIZ / "x.qmd", datos={"estado": estado, **datos}, cuerpo=texto)


def _fuente(resumen: str, pmc: str | None = None) -> Any:
    return lambda pmids: {"1": TextoFuente(resumen, pmc)}


ORACION = "De 93 lactantes, 75 tuvieron parálisis cerebral [@futagi1999]."


def test_una_cifra_que_la_fuente_no_contiene_es_aviso_en_borrador() -> None:
    informe = cotejar(
        [_archivo(ORACION)], {"futagi1999": "1"}, _fuente("Of 93 infants, 70 had CP.")
    )
    assert informe.avisos and not informe.discrepancias


def test_y_discrepancia_en_una_leccion_revisada() -> None:
    archivo = _archivo(ORACION, "revisado")
    informe = cotejar([archivo], {"futagi1999": "1"}, _fuente("Of 93 infants, 70 had CP."))
    assert informe.discrepancias and "75" in informe.discrepancias[0]


def test_la_fuente_con_numeros_en_letras_cuenta() -> None:
    resumen = "Ninety-three infants; the outcomes consisted of cerebral palsy in 75."
    informe = cotejar([_archivo(ORACION, "revisado")], {"futagi1999": "1"}, _fuente(resumen))
    assert informe.discrepancias == []


def test_si_no_esta_en_el_resumen_se_busca_en_el_texto_abierto() -> None:
    informe = cotejar(
        [_archivo(ORACION, "revisado")],
        {"futagi1999": "1"},
        _fuente("Plantar grasp.", "PMC1"),
        lambda pmc: "Of 93 infants, 75 developed cerebral palsy.",
    )
    assert informe.discrepancias == []


def test_una_cifra_cotejada_por_el_revisor_no_se_exige_en_el_resumen() -> None:
    cotejadas = [{"cifra": "75", "clave": "futagi1999", "ubicacion": "tabla 2"}]
    archivo = _archivo(ORACION, "revisado", cifras_cotejadas=cotejadas)
    informe = cotejar([archivo], {"futagi1999": "1"}, _fuente("Of 93 infants."))
    assert informe.discrepancias == []


def test_cifras_cotejadas_exige_una_clave_de_refs() -> None:
    cotejadas = [{"cifra": "75", "clave": "otra2000", "ubicacion": "tabla 2"}]
    with pytest.raises(ValidationError, match="cifras_cotejadas"):
        Leccion.model_validate({**BASE, "cifras_cotejadas": cotejadas})


def test_los_numeros_en_letras_se_leen() -> None:
    assert {"93", "105", "21"} <= numeros_de_fuente(
        "Ninety-three, one hundred and five, twenty one"
    )


# --- 6. referencias del repositorio -------------------------------------------------------------
@pytest.mark.parametrize("ruta", ["lecciones/AI-USE.md", "lecciones/paratextos/declaracion-ia.md"])
def test_la_declaracion_apunta_a_este_repositorio(ruta: str) -> None:
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    assert "alcyedmundo281/neurology" in texto
    assert "uv run" not in texto
    assert "github.com/alcyedmundo281/medsemiotics\n" not in texto
    assert "github.com/alcyedmundo281/medsemiotics." not in texto


# --- hallazgos de la revisión de Codex en el PR #1 ---------------------------------------------
def test_la_condicion_de_la_ficha_es_la_de_la_base(tmp_path: Path) -> None:
    grounding = {"condicion_id": "HM:6004", "concepto_id": "HM:3001", "sensibilidad": 0.95}
    problemas = problemas_de_ficha(_ficha(tmp_path, grounding=grounding), _leer)
    assert any("condicion_id HM:6004" in p for p in problemas)


def test_la_coma_de_miles_de_una_fuente_no_es_decimal() -> None:
    assert "1000" in numeros_de_fuente("1,000 infants")
    assert "1" not in numeros_de_fuente("1,000 infants")
    assert {"14145", "0.97"} <= numeros_de_fuente("Of 14,145 references; r = 0.97")
