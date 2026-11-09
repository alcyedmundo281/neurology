"""Contrato de lecciones (ADR-001): esquema, cuerpo, referencias y verificación de citas."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any

import pytest
import yaml
from pydantic import ValidationError

from lecciones.citas import DoiNoResuelve, RedNoDisponible, Registro, verificar
from lecciones.fuente import RAIZ, EntradaBib, leer_bib
from lecciones.modelo import Leccion, orcid_valido
from lecciones.validacion import SECCIONES, problemas_de_cuerpo, validar_archivo

if TYPE_CHECKING:
    from pathlib import Path

ABSTRACT = " ".join(["palabra"] * 50)

BASE: dict[str, Any] = {
    "id": "leccion-prueba",
    "tipo": "leccion",
    "titulo": "Lección de prueba",
    "parte": "neonato",
    "orden": 1,
    "estado": "borrador",
    "autores": [
        {
            "nombre": "Alcy Torres Catefort",
            "rol_obra": "autor-fundador",
            "fallecido": True,
            "credit": ["conceptualizacion"],
        },
        {
            "nombre": "Alcy Ramiro Torres Guerrero",
            "orcid": "0000-0002-9742-375X",
            "credit": ["redaccion", "revision-edicion"],
        },
    ],
    "uso_ia": ["transcripcion", "redaccion-borrador"],
    "legado": {"obra": "Neurología Pediátrica, 1993", "paginas": "16"},
    "pregunta_clinica": "¿Es normal la prensión plantar de este recién nacido?",
    "abstract": ABSTRACT,
    "dialogo_clinico": "Un recién nacido de 36 horas con prensión plantar débil a la izquierda.",
    "indispensable": ["La prensión plantar debe ser simétrica."],
    "limites": ["Un niño dormido o llorando no permite valorar el reflejo."],
    "conceptos": ["HM:1234"],
    "refs": ["futagi1999"],
}

BIB = {
    "futagi1999": EntradaBib(
        clave="futagi1999",
        pmid="10082338",
        doi="10.1016/s0887-8994(98)00103-9",
        titulo="Clinical significance of plantar grasp response in infants.",
    )
}


def cuerpo(**reemplazos: str) -> str:
    textos = {s: f"Texto de la sección {s.lower()}." for s in SECCIONES}
    textos.update(reemplazos)
    partes = [f"## {s}\n\n{textos[s]}\n" for s in SECCIONES if textos[s] is not None]
    partes.append(
        "::: {.legado}\n*«Consiste en realizar con el dedo pulgar una presión.»* — p. 16\n:::\n"
    )
    return "\n".join(partes)


def escribir(tmp_path: Path, datos: dict[str, Any], texto: str) -> Path:
    ruta = tmp_path / f"{datos['id']}.qmd"
    contenido = "---\n" + yaml.safe_dump(datos, allow_unicode=True) + "---\n" + texto
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


# --- esquema -------------------------------------------------------------------------------


def test_orcid_con_digito_de_control() -> None:
    assert orcid_valido("0000-0002-9742-375X")
    assert orcid_valido("0000-0002-9742-375X")
    assert not orcid_valido("0000-0001-5798-9162")
    assert not orcid_valido("0000-0001-5798")


def test_leccion_valida() -> None:
    leccion = Leccion.model_validate(BASE)
    assert leccion.autores[0].rol_obra == "autor-fundador"


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"estado": "revisado"}, "revisor"),
        ({"estado": "revisado", "revisor": "Claude", "fecha_revision": "2026-11-01"}, "persona"),
        ({"estado": "revisado", "revisor": "Ramiro Torres"}, "fecha_revision"),
        ({"abstract": "demasiado corto para un resumen"}, "40 y 80"),
        ({"legado": None}, "legado"),
        ({"indispensable": ["a", "b", "c", "d", "e", "f"]}, "at most 5"),
        ({"refs": ["futagi1999", "futagi1999"]}, "repetidos"),
    ],
)
def test_reglas_del_esquema(cambio: dict[str, Any], mensaje: str) -> None:
    with pytest.raises(ValidationError, match=mensaje):
        Leccion.model_validate({**BASE, **cambio})


def test_revisado_con_revisor_humano() -> None:
    datos = {**BASE, "estado": "revisado", "revisor": "Alcy Ramiro Torres Guerrero"}
    assert Leccion.model_validate({**datos, "fecha_revision": "2026-11-01"}).estado == "revisado"


def test_autor_fallecido_no_revisa_la_edicion_nueva() -> None:
    autores = [{**BASE["autores"][0], "credit": ["conceptualizacion", "revision-edicion"]}]
    with pytest.raises(ValidationError, match="fallecido"):
        Leccion.model_validate({**BASE, "autores": autores})


@pytest.mark.parametrize(
    ("medio", "valido"),
    [
        (
            {"origen": "commons", "fuente_url": "https://commons.wikimedia.org/wiki/File:X.png"},
            True,
        ),
        ({"origen": "commons", "fuente_url": "https://example.org/x.png"}, False),
        ({"origen": "ilustracion-original", "autor_ilustracion": "Ilustradora"}, True),
        ({"origen": "ilustracion-original"}, False),
    ],
)
def test_procedencia_de_imagenes(medio: dict[str, Any], valido: bool) -> None:
    base = {
        "id": "fig-1",
        "tipo": "imagen",
        "archivo_local": "assets/img/x.png",
        "pie": "Pie",
        "licencia": "CC BY-SA 4.0",
        "credito": "Autor",
    }
    datos = {**BASE, "medios": [{**base, **medio}]}
    if valido:
        Leccion.model_validate(datos)
    else:
        with pytest.raises(ValidationError):
            Leccion.model_validate(datos)


# --- cuerpo --------------------------------------------------------------------------------


def test_cuerpo_conforme() -> None:
    assert problemas_de_cuerpo(cuerpo(), Leccion.model_validate(BASE)) == []


def test_seccion_ausente_y_vacia() -> None:
    texto = cuerpo().replace("## Cómo prevenir", "## Otra cosa")
    texto = texto.replace("Texto de la sección nuestra realidad.", "")
    problemas = problemas_de_cuerpo(texto, Leccion.model_validate(BASE))
    assert any("Cómo prevenir" in p for p in problemas)
    assert any("Nuestra realidad: sección vacía" in p for p in problemas)


@pytest.mark.parametrize(
    "texto",
    [
        "El LR positivo es 3,5 para meningitis.",
        "Tiene sensibilidad de 98 % para parálisis cerebral.",
        "Con IC 95 % de 2,0 a 6,0.",
    ],
)
def test_metricas_a_mano_bloquean(texto: str) -> None:
    problemas = problemas_de_cuerpo(cuerpo(**{"Qué significa": texto}), None)
    assert any("a mano" in p for p in problemas)


def test_cifra_sin_cita_y_con_cita() -> None:
    leccion = Leccion.model_validate(BASE)
    sin = cuerpo(**{"Qué significa": "De 93 lactantes, 75 desarrollaron parálisis cerebral."})
    con = cuerpo(**{"Qué significa": "De 93 lactantes, 75 la desarrollaron [@futagi1999]."})
    assert any("cifra sin cita" in p for p in problemas_de_cuerpo(sin, leccion))
    assert problemas_de_cuerpo(con, leccion) == []


def test_tokens_deben_declarar_su_concepto() -> None:
    leccion = Leccion.model_validate(BASE)
    ok = cuerpo(**{"Qué significa": "Rinde {{lr+ HM:1234}}."})
    ajeno = cuerpo(**{"Qué significa": "Rinde {{lr+ HM:9999}}."})
    assert problemas_de_cuerpo(ok, leccion) == []
    assert any("no figura en «conceptos»" in p for p in problemas_de_cuerpo(ajeno, leccion))


def test_cita_no_declarada() -> None:
    texto = cuerpo(**{"Qué significa": "Hay 2 series [@otra2020]."})
    assert any(
        "no declarada" in p for p in problemas_de_cuerpo(texto, Leccion.model_validate(BASE))
    )


def test_legado_declarado_exige_bloque() -> None:
    texto = cuerpo().split("::: {.legado}")[0]
    problemas = problemas_de_cuerpo(texto, Leccion.model_validate(BASE))
    assert any("{.legado}" in p for p in problemas)


# --- archivo completo ----------------------------------------------------------------------


def test_borrador_incompleto_solo_alerta(tmp_path: Path) -> None:
    datos = {**BASE, "limites": []}
    r = validar_archivo(escribir(tmp_path, datos, cuerpo()), tmp_path, BIB)
    assert r.errores == []
    assert any("limites" in a for a in r.alertas)


def test_revisado_incompleto_bloquea(tmp_path: Path) -> None:
    datos = {
        **BASE,
        "estado": "revisado",
        "revisor": "Alcy Ramiro Torres Guerrero",
        "fecha_revision": "2026-11-01",
    }
    r = validar_archivo(escribir(tmp_path, datos, cuerpo(**{"Qué hacer": ""})), tmp_path, {})
    assert any("Qué hacer" in e for e in r.errores)
    assert any("no está en lecciones/refs.bib" in e for e in r.errores)


def test_nombre_de_archivo_igual_al_id(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, BASE, cuerpo())
    otra = ruta.with_name("otro-nombre.qmd")
    ruta.rename(otra)
    assert any("debe llamarse" in e for e in validar_archivo(otra, tmp_path, BIB).errores)


def test_plantilla_es_un_borrador_conforme(tmp_path: Path) -> None:
    destino = tmp_path / "leccion-ejemplo.qmd"
    shutil.copy(RAIZ / "assets" / "plantilla-leccion.qmd", destino)
    assert validar_archivo(destino, tmp_path, {}).errores == []


def test_bibliografia_del_repositorio_se_lee() -> None:
    assert isinstance(leer_bib(), dict)


# --- verificación de citas (sin red: autoridades simuladas) ---------------------------------


def _pubmed(doi: str) -> Any:
    def consultar(pmids: list[str]) -> dict[str, Registro]:
        return {
            p: Registro(doi=doi, titulo="Clinical significance of plantar grasp") for p in pmids
        }

    return consultar


def test_citas_verificadas() -> None:
    doi = BIB["futagi1999"].doi
    informe = verificar(
        BIB, _pubmed(doi), lambda d: Registro(doi=d, titulo="Clinical significance"), pausa=0
    )
    assert informe.verificadas == ["futagi1999"]
    assert informe.codigo == 0


def test_citas_doi_distinto_en_pubmed() -> None:
    informe = verificar(BIB, _pubmed("10.9999/otro"), lambda d: Registro(d, ""), pausa=0)
    assert informe.codigo == 1


def test_citas_doi_que_crossref_no_conoce() -> None:
    def no_resuelve(_: str) -> Registro:
        raise DoiNoResuelve(404)

    informe = verificar(BIB, _pubmed(BIB["futagi1999"].doi), no_resuelve, pausa=0)
    assert informe.codigo == 1


def test_citas_sin_red_quedan_incompletas() -> None:
    def caida(_: list[str]) -> dict[str, Registro]:
        raise RedNoDisponible("timeout")

    assert verificar(BIB, caida, lambda d: Registro(d, ""), pausa=0).codigo == 2


# --- mapa del libro -------------------------------------------------------------------------


def test_mapa_del_repositorio_cubre_los_modulos_de_clase() -> None:
    from lecciones import mapa as m

    mapa = m.cargar()
    assert len(m.modulos_publicados()) == 13
    assert m.coherencia(mapa, {}) == []


def test_esqueleto_es_un_borrador_coherente(tmp_path: Path) -> None:
    from lecciones import mapa as m

    mapa = m.cargar()
    ident = "leccion-examen-neurologico-recien-nacido"
    ruta = tmp_path / f"{ident}.qmd"
    ruta.write_text(m.esqueleto(mapa, ident), encoding="utf-8")
    r = validar_archivo(ruta, RAIZ, {})
    assert r.errores == []
    assert any("PENDIENTE" in a for a in r.alertas)
    assert m.coherencia(mapa, m.estados([ruta])) == []


def test_mapa_detecta_desvios(tmp_path: Path) -> None:
    from lecciones import mapa as m

    mapa = m.cargar()
    ident = "leccion-cefaleas"
    ruta = tmp_path / f"{ident}.qmd"
    texto = m.esqueleto(mapa, ident).replace("orden: 1", "orden: 7", 1)
    ruta.write_text(texto, encoding="utf-8")
    errores = m.coherencia(mapa, m.estados([ruta]))
    assert any("orden" in e for e in errores)
    huerfana = tmp_path / "leccion-sin-mapa.qmd"
    huerfana.write_text(texto.replace(ident, "leccion-sin-mapa"), encoding="utf-8")
    assert any("no figura" in e for e in m.coherencia(mapa, m.estados([huerfana])))


def test_mapa_rechaza_modulo_en_dos_lecciones() -> None:
    from lecciones import mapa as m

    datos = yaml.safe_load(m.MAPA.read_text(encoding="utf-8"))
    datos["lecciones"][1]["modulos_html"] = ["neurologia/demencias.html"]
    with pytest.raises(ValidationError, match="más de una lección"):
        m.Mapa.model_validate(datos)


# --- hallazgos de la revisión del PR #34 ----------------------------------------------------


def test_cita_agrupada_valida_cada_clave() -> None:
    texto = cuerpo(**{"Qué significa": "Hay 20 casos [@otra2020; @futagi1999]."})
    problemas = problemas_de_cuerpo(texto, Leccion.model_validate(BASE))
    assert any("[@otra2020] no declarada" in p for p in problemas)


def test_clave_de_cita_no_cuenta_como_metrica() -> None:
    datos = {**BASE, "refs": ["futagi1999"]}
    texto = cuerpo(**{"Qué significa": "La sensibilidad es {{sens HM:1234}} [@futagi1999]."})
    assert problemas_de_cuerpo(texto, Leccion.model_validate(datos)) == []


@pytest.mark.parametrize(
    ("campo", "valor", "motivo"),
    [
        ("indispensable", ["La sensibilidad es 98 %."], "a mano"),
        ("abstract", ABSTRACT + " con un LR de 8 para la condición", "a mano"),
        ("limites", ["Falla en 3 de cada 10 niños."], "cifra sin cita"),
        ("indispensable", ["Rinde {{lr+ HM:9999}}."], "no figura en «conceptos»"),
    ],
)
def test_frontmatter_clinico_sigue_las_reglas_de_evidencia(
    campo: str, valor: Any, motivo: str
) -> None:
    from lecciones.validacion import problemas_de_frontmatter

    problemas = problemas_de_frontmatter(Leccion.model_validate({**BASE, campo: valor}))
    assert any(motivo in p for p in problemas)


def test_vineta_admite_datos_del_paciente() -> None:
    from lecciones.validacion import problemas_de_frontmatter

    assert problemas_de_frontmatter(Leccion.model_validate(BASE)) == []


def test_legado_fuera_de_las_partes_pediatricas_lleva_al_fundador(tmp_path: Path) -> None:
    from lecciones import mapa as m

    mapa = m.cargar()
    ident = "leccion-perdida-visual-aguda-neuropatias-opticas"
    texto = m.esqueleto(mapa, ident)
    assert "Alcy Torres Catefort" in texto
    ruta = tmp_path / f"{ident}.qmd"
    ruta.write_text(texto, encoding="utf-8")
    assert m.coherencia(mapa, m.estados([ruta])) == []
    assert validar_archivo(ruta, RAIZ, {}).errores == []


# --- declaración de uso de IA ---------------------------------------------------------------


def test_cada_leccion_declara_su_uso_de_ia() -> None:
    datos = {k: v for k, v in BASE.items() if k != "uso_ia"}
    with pytest.raises(ValidationError, match="uso_ia"):
        Leccion.model_validate(datos)
    assert Leccion.model_validate({**BASE, "uso_ia": []}).uso_ia == []
    with pytest.raises(ValidationError):
        Leccion.model_validate({**BASE, "uso_ia": ["imagenes"]})


def test_la_obra_no_sale_sin_declaracion(tmp_path: Path) -> None:
    from lecciones.validacion import problemas_de_declaracion

    assert problemas_de_declaracion(RAIZ) == []
    problemas = problemas_de_declaracion(tmp_path)
    assert any("AI-USE.md" in p for p in problemas)
    assert any("colofón" in p for p in problemas)


def test_el_esqueleto_declara_la_transcripcion_del_legado() -> None:
    from lecciones import mapa as m

    texto = m.esqueleto(m.cargar(), "leccion-examen-neurologico-recien-nacido")
    assert "- transcripcion" in texto


# --- sílabo -------------------------------------------------------------------------------


def test_el_silabo_del_curso_esta_cubierto_por_el_mapa() -> None:
    from lecciones import mapa as m

    mapa = m.cargar()
    assert mapa.silabo is not None
    assert [s.semana for s in mapa.silabo.semanas] == list(range(1, 19))


def test_una_semana_sin_leccion_del_mapa_bloquea() -> None:
    from lecciones import mapa as m

    datos = yaml.safe_load(m.MAPA.read_text(encoding="utf-8"))
    datos["silabo"]["semanas"][4]["lecciones"] = ["leccion-inexistente"]
    with pytest.raises(ValidationError, match="fuera del mapa"):
        m.Mapa.model_validate(datos)
