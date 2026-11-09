"""Autoría del libro: sale de lecciones/mapa.yaml, sin valores de respaldo ni nombres inventados."""

from __future__ import annotations

import re
import shutil
from typing import TYPE_CHECKING

import pytest
import yaml

from libro.datos import RAIZ, MetadatosLibro, leer_metadatos
from libro.qmd import generar_proyecto_quarto

if TYPE_CHECKING:
    from pathlib import Path

AUTORES = [
    "Alcy Torres Catefort †",
    "Alcy Ramiro Torres Guerrero",
    "Gladys Torres Guerrero",
    "Alcy Edmundo Torres Guerrero",
    "Daniela Torres Tobar",
]


def en_orden(texto: str, nombres: list[str]) -> bool:
    """¿Aparecen todos los nombres en el texto, en ese orden?"""
    posicion = 0
    for nombre in nombres:
        encontrado = texto.find(nombre, posicion)
        if encontrado < 0:
            return False
        posicion = encontrado + len(nombre)
    return True


# --- portada y créditos ----------------------------------------------------------------------


def test_el_orden_de_los_autores_se_comprueba() -> None:
    assert en_orden(" ".join(AUTORES), AUTORES)
    assert not en_orden(" ".join(reversed(AUTORES)), AUTORES)
    assert not en_orden(" ".join(AUTORES[:3]), AUTORES)


def test_los_metadatos_traen_los_cinco_autores_en_su_orden() -> None:
    meta = leer_metadatos(RAIZ)
    assert meta.nombres_autores == AUTORES
    assert meta.autores[0].fallecido
    assert [a.orcid for a in meta.autores] == [
        None,
        None,
        None,
        "0000-0002-9742-375X",
        None,
    ]
    assert meta.autores[-1].rol == "autora de las autoevaluaciones"
    assert meta.autores_autoevaluaciones == ("Daniela Torres Tobar",)
    assert meta.revisor_autoevaluaciones == "Alcy Edmundo Torres Guerrero"
    assert meta.licencia == "CC BY-NC-SA 4.0"


def test_portada_y_creditos_llevan_los_cinco_autores_en_ese_orden(tmp_path: Path) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    portadilla = index.split("{.portadilla-pdf}")[1].split("{.creditos-pdf}")[0]
    creditos = index.split("{.creditos-pdf}")[1].split("{.alerta-ficha}")[0]
    assert en_orden(portadilla, AUTORES), "la portadilla no lleva los cinco autores en orden"
    assert en_orden(creditos, AUTORES), "los créditos no llevan los cinco autores en orden"
    assert "**Autoevaluaciones:** Daniela Torres Tobar, de toda la obra." in creditos
    portada_tex = (tmp_path / "datos-libro.tex").read_text(encoding="utf-8")
    assert en_orden(portada_tex, AUTORES), "la portada impresa no lleva los cinco autores"
    portada_svg = (tmp_path / "portada.svg").read_text(encoding="utf-8")
    assert en_orden(portada_svg, AUTORES), "la portada (SVG) no lleva los cinco autores"


def test_el_preambulo_no_escribe_ningun_nombre_de_autor() -> None:
    preambulo = (RAIZ / "assets" / "libro" / "preambulo.tex").read_text(encoding="utf-8")
    assert "libroautoresportada" in preambulo
    assert not any(nombre.removesuffix(" †") in preambulo for nombre in AUTORES)


def test_los_creditos_declaran_que_la_revision_del_editor_no_es_independiente(
    tmp_path: Path,
) -> None:
    meta = leer_metadatos(RAIZ)
    assert meta.editor.nombre == "Alcy Edmundo Torres Guerrero"
    assert meta.partes_del_editor == (
        "Fundamentos: la semiología basada en la evidencia",
        "El adulto: síndromes y urgencias",
    )
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    creditos = (tmp_path / "index.qmd").read_text(encoding="utf-8").split("{.creditos-pdf}")[1]
    assert "el editor es también autor; su revisión de esas partes no es independiente" in creditos
    assert "Fundamentos: la semiología basada en la evidencia" in creditos
    assert "El adulto: síndromes y urgencias" in creditos
    # En neonato, lactante-niño y neuroftalmología el autor es otro: ahí sí revisa un tercero.
    assert "El recién nacido" not in creditos.split("Revisión editorial:")[1].split("DOI")[0]


def test_creditos_nueva_edicion_sin_doi_de_la_obra(tmp_path: Path) -> None:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    creditos = index.split("{.creditos-pdf}")[1]
    assert "Primera edición" not in index
    assert "Nueva edición, que continúa la obra de Alcy Torres Catefort" in creditos
    assert "Neuropediatría–Urgencias" in creditos
    assert "Neurología Pediátrica. 2.ª ed." in creditos
    assert "DOI de la obra: pendiente" in creditos
    assert "ISBN: pendiente" in creditos
    assert "zenodo" not in index.lower()
    assert "Atribución-NoComercial-CompartirIgual 4.0" in creditos
    assert "CC BY-NC-SA 4.0" in creditos


# --- sin valores de respaldo -----------------------------------------------------------------


def _raiz_copia(tmp_path: Path) -> Path:
    (tmp_path / "lecciones").mkdir()
    shutil.copyfile(RAIZ / "lecciones" / "mapa.yaml", tmp_path / "lecciones" / "mapa.yaml")
    shutil.copyfile(RAIZ / "CITATION.cff", tmp_path / "CITATION.cff")
    return tmp_path


def _cambiar_mapa(raiz: Path, cambio: object) -> None:
    ruta = raiz / "lecciones" / "mapa.yaml"
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    cambio(datos)  # type: ignore[operator]
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")


def test_la_copia_de_prueba_es_valida(tmp_path: Path) -> None:
    assert isinstance(leer_metadatos(_raiz_copia(tmp_path)), MetadatosLibro)


def test_falla_sin_mapa(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="falta el mapa del libro"):
        leer_metadatos(tmp_path)


def test_falla_sin_subtitulo(tmp_path: Path) -> None:
    raiz = _raiz_copia(tmp_path)
    _cambiar_mapa(raiz, lambda d: d["obra"].pop("subtitulo"))
    with pytest.raises(ValueError, match="obra.subtitulo"):
        leer_metadatos(raiz)


def test_falla_si_el_primer_autor_no_es_el_fundador(tmp_path: Path) -> None:
    raiz = _raiz_copia(tmp_path)

    def invertir(d: dict[str, dict[str, object]]) -> None:
        d["personas"] = dict(reversed(list(d["personas"].items())))

    _cambiar_mapa(raiz, invertir)
    with pytest.raises(ValueError, match="autor fundador"):
        leer_metadatos(raiz)


def test_falla_sin_el_repositorio_en_citation_cff(tmp_path: Path) -> None:
    clave = "repository-code"
    raiz = _raiz_copia(tmp_path)
    ruta = raiz / "CITATION.cff"
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    del datos[clave]
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match=clave):
        leer_metadatos(raiz)


# --- ningún nombre ni ORCID fuera del mapa -----------------------------------------------------

ORCID = re.compile(r"\b[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]\b")
CAPITALIZADA = "[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
SECUENCIA = re.compile(rf"(?:Dra?\.\s+)?{CAPITALIZADA}(?:\s+{CAPITALIZADA})*")
# Palabras que delatan un nombre de la familia de la obra: si aparece una, la secuencia completa
# de palabras con mayúscula inicial tiene que ser un nombre de lecciones/mapa.yaml (personas).
ANCLAS = {"Alcy", "Gladys", "Torres", "Guerrero", "Catefort", "Ramiro", "Edmundo"}
SUFIJOS = {".py", ".md", ".qmd", ".tex", ".yaml", ".yml", ".json", ".lua", ".mjs", ".cjs"}
SUFIJOS |= {".js", ".html", ".bib", ".txt", ".cff", ".csv", ".svg"}
CARPETAS = ("assets", "tools", "lecciones")
GENERADO = "assets/data/"  # JSON derivados de posts/ y casos/, que no son del libro
# Este archivo trae a propósito nombres falsos para probar el detector.
ESTE_ARCHIVO = "tools/tests/test_autoria.py"

# Excepciones explícitas y mínimas. Cada una se escribe partida para que este archivo no sea,
# él mismo, una aparición del nombre o del ORCID inventados.
NOMBRE_INVENTADO = "Alcy" + " " + "Montserrat"
ORCID_INVENTADO = "0009-0001-" + "7627-9895"
ORCID_DE_PRUEBA_INVALIDO = "0000-0001-5798-" + "9162"  # prueba del dígito de control
EXCEPCIONES: dict[str, set[str]] = {
    "lecciones/AI-USE.md": {NOMBRE_INVENTADO, ORCID_INVENTADO},  # solo en «Qué ya falló»
    "tools/tests/test_lecciones.py": {ORCID_DE_PRUEBA_INVALIDO},
}


def _personas() -> tuple[list[set[str]], set[str]]:
    datos = yaml.safe_load((RAIZ / "lecciones" / "mapa.yaml").read_text(encoding="utf-8"))
    personas = list(datos["personas"].values())
    nombres = [set(p["nombre"].split()) for p in personas]
    orcids = {p["orcid"] for p in personas if p.get("orcid")}
    return nombres, orcids


def intrusos(texto: str, nombres: list[set[str]], orcids: set[str]) -> list[str]:
    """Nombres de la familia de la obra y ORCID que no pertenecen a ninguna persona del mapa."""
    encontrados = [o for o in ORCID.findall(texto) if o not in orcids]
    for secuencia in SECUENCIA.findall(texto):
        palabras = [w for w in secuencia.split() if w not in ("Dr.", "Dra.")]
        if ANCLAS.isdisjoint(palabras) and "Montserrat" not in palabras:
            continue
        if not any(set(palabras) <= nombre for nombre in nombres):
            encontrados.append(" ".join(palabras))
    return encontrados


def test_el_detector_de_intrusos_funciona() -> None:
    nombres, orcids = _personas()
    assert intrusos("Alcy Ramiro Torres Guerrero", nombres, orcids) == []
    assert intrusos("Dr. Alcy Torres", nombres, orcids) == []
    assert intrusos("Torres Catefort A.", nombres, orcids) == []
    assert intrusos(NOMBRE_INVENTADO, nombres, orcids) == [NOMBRE_INVENTADO]
    assert intrusos(f"ORCID {ORCID_INVENTADO}", nombres, orcids) == [ORCID_INVENTADO]
    assert intrusos("Daniela Torres Tobar", nombres, orcids) == []
    assert intrusos("Juan Torres", nombres, orcids) == ["Juan Torres"]
    assert intrusos("Gladys Montserrat", nombres, orcids) == ["Gladys Montserrat"]


def _archivos() -> list[Path]:
    salida: list[Path] = []
    for carpeta in CARPETAS:
        for ruta in sorted((RAIZ / carpeta).rglob("*")):
            relativa = ruta.relative_to(RAIZ).as_posix()
            if not ruta.is_file() or ruta.suffix not in SUFIJOS:
                continue
            if relativa in (ESTE_ARCHIVO,) or relativa.startswith(GENERADO):
                continue
            if "node_modules" in relativa:
                continue
            salida.append(ruta)
    return salida


def _sin_excepcion(relativa: str, texto: str) -> str:
    permitidos = EXCEPCIONES.get(relativa, set())
    if relativa == "lecciones/AI-USE.md":
        # Solo se tolera dentro de «Qué ya falló»: antes de esa sección sigue contando.
        antes, _, despues = texto.partition("## Qué ya falló")
        for valor in permitidos:
            despues = despues.replace(valor, "")
        return antes + despues
    for valor in permitidos:
        texto = texto.replace(valor, "")
    return texto


def test_ningun_nombre_ni_orcid_fuera_del_mapa_en_assets_tools_o_lecciones() -> None:
    nombres, orcids = _personas()
    problemas: list[str] = []
    for ruta in _archivos():
        relativa = ruta.relative_to(RAIZ).as_posix()
        texto = _sin_excepcion(relativa, ruta.read_text(encoding="utf-8", errors="ignore"))
        problemas += [f"{relativa}: {valor}" for valor in intrusos(texto, nombres, orcids)]
    assert not problemas, "personas u ORCID que no están en lecciones/mapa.yaml:\n" + "\n".join(
        problemas
    )


def _creditos(tmp_path: Path) -> str:
    generar_proyecto_quarto(tmp_path, RAIZ, exigir_semblanzas=False)
    index = (tmp_path / "index.qmd").read_text(encoding="utf-8")
    return index.split("{.creditos-pdf}")[1]


def test_los_creditos_traen_el_contacto_editorial(tmp_path: Path) -> None:
    creditos = _creditos(tmp_path)
    assert "Comentarios, erratas y permisos: <alcy.torres@powersemiotics.com>" in creditos


def test_los_creditos_no_traen_el_correo_de_ningun_autor(tmp_path: Path) -> None:
    creditos = _creditos(tmp_path)
    assert re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", creditos) == ["alcy.torres@powersemiotics.com"]
    meta = leer_metadatos(RAIZ)
    assert meta.contacto == "alcy.torres@powersemiotics.com"


def test_creditos_separan_la_obra_de_la_plataforma(tmp_path: Path) -> None:
    creditos = _creditos(tmp_path)
    assert "DOI de la obra: pendiente de asignación." in creditos
    assert "Editor de la obra: pendiente del acuerdo escrito de los herederos." in creditos
    assert "Plataforma complementaria: *medsemiotics*" in creditos
