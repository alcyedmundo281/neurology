"""CLI: ``python -m lecciones <orden>``.

- ``check``: contrato de todas las lecciones, coherencia con ``lecciones/mapa.yaml`` y
  ``mapa-maestro-libro.md`` al día, y que todo token de evidencia resuelva contra ``posts/`` y
  ``lecciones/evidencia/``, de una sola revisión de la db (sin red).
- ``mapa``: regenera ``mapa-maestro-libro.md`` desde el mapa y el estado de las lecciones.
- ``nuevo <id>``: crea ``lecciones/<id>.qmd`` en borrador desde su fila del mapa.
- ``proyectar <id>``: escribe la lección con sus tokens resueltos (``build/lecciones/<id>.qmd``
  y ``refs.bib``), lista para ``quarto render``; aborta si un token no resuelve.
- ``citas``: verifica ``lecciones/refs.bib`` contra PubMed y Crossref y coteja cada cifra citada
  con el texto de su fuente (requiere red).
- ``evidencia``: comprueba que las fichas de evidencia sean las de medsemiotics-db en su revisión
  fijada (necesita una copia git de la db: ``--db`` o ``NEUROLOGY_DB``; sin red).
- ``legado``: lista las citas literales de 1993 con su resumen SHA-256 y su estado de cotejo.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from casos.errores import ErrorDeCaso
from pydantic import ValidationError

from lecciones import legado
from lecciones import mapa as mapa_libro
from lecciones.cifras import cotejar
from lecciones.citas import verificar
from lecciones.evidencia import cargar_articulos
from lecciones.fuente import CARPETA, RAIZ, ErrorDeFuente, archivos, leer, leer_bib
from lecciones.integridad import lector_git, problemas_de_fichas
from lecciones.proyectar import escribir_proyeccion, problemas_de_resolucion
from lecciones.validacion import _limpio, validar_todo


def _cargar_mapa() -> mapa_libro.Mapa | None:
    try:
        return mapa_libro.cargar()
    except (ErrorDeFuente, ValidationError) as exc:
        print(f"✗ lecciones/mapa.yaml: {exc}")
        return None


SALIDA_PROYECCION = RAIZ / "build" / "lecciones"


def _problemas_de_tokens(rutas: list[Path]) -> list[str]:
    """Todo token debe resolver contra los artículos de ``posts/`` y ``lecciones/evidencia/``."""
    try:
        articulos = cargar_articulos()
    except ErrorDeCaso as exc:
        return [f"evidencia: {exc}"]
    problemas: list[str] = []
    for ruta in rutas:
        try:
            archivo = leer(ruta)
        except ErrorDeFuente:
            continue  # ya lo informa validar_todo
        problemas += [f"{ruta.name}: {p}" for p in problemas_de_resolucion(archivo, articulos)]
    return problemas


def _cotejo_legado(
    rutas: list[Path], mapa: mapa_libro.Mapa
) -> tuple[list[str], list[str], list[tuple[str, str, legado.CitaLegado, bool]]]:
    """Errores, alertas y la lista de citas legado con su estado de cotejo."""
    try:
        registro = legado.cargar_registro()
    except ErrorDeFuente as exc:
        return [str(exc)], [], []
    vivas = {p.nombre for p in mapa.personas.values() if not p.fallecido}
    errores: list[str] = []
    alertas: list[str] = []
    listado: list[tuple[str, str, legado.CitaLegado, bool]] = []
    vigentes: dict[str, set[str]] = {}
    for ruta in rutas:
        try:
            archivo = leer(ruta)
        except ErrorDeFuente:
            continue
        ident = str(archivo.datos.get("id"))
        encontradas, _ = legado.citas(_limpio(archivo.cuerpo))
        vigentes[ident] = {c.sha for c in encontradas}
        problemas = legado.problemas_de_cotejo(ident, encontradas, registro, vivas)
        borrador = archivo.datos.get("estado", "borrador") == "borrador"
        (alertas if borrador else errores).extend(f"{ruta.name}: {p}" for p in problemas)
        cotejadas = {c.sha256 for c in registro.cotejos if c.leccion == ident}
        listado += [(ident, ruta.name, c, c.sha in cotejadas) for c in encontradas]
    errores += legado.huerfanos(registro, vigentes)
    return errores, alertas, listado


def _check() -> int:
    rutas = archivos()
    resultado = validar_todo(rutas)
    errores = list(resultado.errores)
    errores += _problemas_de_tokens(rutas)
    mapa = _cargar_mapa()
    if mapa is None:
        return 1
    errores_legado, alertas_legado, _ = _cotejo_legado(rutas, mapa)
    errores += errores_legado
    resultado.alertas += alertas_legado
    estados = mapa_libro.estados(rutas)
    errores += mapa_libro.coherencia(mapa, estados)
    esperado = mapa_libro.renderizar(mapa, estados)
    actual = mapa_libro.SALIDA.read_text(encoding="utf-8") if mapa_libro.SALIDA.is_file() else ""
    if actual != esperado:
        errores.append("mapa-maestro-libro.md desactualizado: python -m lecciones mapa")
    for alerta in resultado.alertas:
        print(f"⚠ {alerta}")
    for error in errores:
        print(f"✗ {error}")
    if errores:
        print(f"lecciones: {len(errores)} errores en {len(rutas)} lecciones")
        return 1
    print(
        f"lecciones: {len(rutas)} de {len(mapa.lecciones)} lecciones del mapa conformes "
        f"({len(resultado.alertas)} alertas)"
    )
    return 0


def _mapa() -> int:
    mapa = _cargar_mapa()
    if mapa is None:
        return 1
    mapa_libro.SALIDA.write_text(
        mapa_libro.renderizar(mapa, mapa_libro.estados()), encoding="utf-8"
    )
    print(f"escrito {mapa_libro.SALIDA.relative_to(RAIZ)}")
    return 0


def _nuevo(ident: str) -> int:
    mapa = _cargar_mapa()
    if mapa is None:
        return 1
    destino = CARPETA / f"{ident}.qmd"
    if destino.exists():
        print(f"✗ ya existe {destino.relative_to(RAIZ)}: no se sobrescribe")
        return 1
    try:
        texto = mapa_libro.esqueleto(mapa, ident)
    except ErrorDeFuente as exc:
        print(f"✗ {exc}")
        return 1
    destino.write_text(texto, encoding="utf-8")
    print(f"creado {destino.relative_to(RAIZ)} (borrador); regenere el mapa con «mapa»")
    return 0


def _proyectar(ident: str, salida: Path) -> int:
    ruta = CARPETA / f"{ident}.qmd"
    if not ruta.is_file():
        print(f"✗ no existe {ruta.relative_to(RAIZ)}")
        return 1
    try:
        destino = escribir_proyeccion(ruta, salida, cargar_articulos())
    except ErrorDeCaso as exc:
        print(f"✗ {ident}: {exc}")
        return 1
    print(f"escrito {destino}; compile con: quarto render {destino.name}")
    return 0


def _citas() -> int:
    try:
        bib = leer_bib()
    except ErrorDeFuente as exc:
        print(f"✗ {exc}")
        return 1
    informe = verificar(bib)
    lecciones_leidas = []
    for ruta in archivos():
        try:
            lecciones_leidas.append(leer(ruta))
        except ErrorDeFuente as exc:
            informe.discrepancias.append(str(exc))
    cifras = cotejar(lecciones_leidas, {c: e.pmid for c, e in bib.items() if e.pmid.isdigit()})
    informe.discrepancias += cifras.discrepancias
    informe.incompletas += cifras.incompletas
    for aviso in informe.avisos + cifras.avisos:
        print(f"⚠ {aviso}")
    for linea in informe.discrepancias:
        print(f"✗ {linea}")
    for linea in informe.incompletas:
        print(f"… {linea}")
    print(
        f"refs.bib: {len(informe.verificadas)}/{len(bib)} verificadas en PubMed y Crossref; "
        f"cifras: {len(cifras.discrepancias)} discrepancias, {len(cifras.avisos)} avisos"
        + (" (INCOMPLETA)" if informe.incompletas else "")
    )
    return informe.codigo


def _evidencia(db: Path | None) -> int:
    if db is None or not (db / ".git").exists():
        print(
            "✗ indique una copia git completa de medsemiotics-db con --db o NEUROLOGY_DB "
            "(git clone https://github.com/alcyedmundo281/medsemiotics-db)"
        )
        return 1
    rutas = sorted((RAIZ / "posts").glob("*.md")) + sorted((CARPETA / "evidencia").glob("*.md"))
    problemas = problemas_de_fichas(rutas, lector_git(db))
    for p in problemas:
        print(f"✗ {p}")
    if problemas:
        print(f"evidencia: {len(problemas)} problemas en {len(rutas)} fichas")
        return 1
    print(f"evidencia: {len(rutas)} fichas idénticas a medsemiotics-db en su revisión fijada")
    return 0


def _legado() -> int:
    mapa = _cargar_mapa()
    if mapa is None:
        return 1
    errores, _, listado = _cotejo_legado(archivos(), mapa)
    for ident, _archivo, cita, cotejada in listado:
        marca = "✓ cotejada" if cotejada else "· sin cotejar"
        print(f"{marca}  {ident}  p. {cita.paginas}  sha256 {cita.sha}\n    «{cita.texto[:80]}…»")
    for error in errores:
        print(f"✗ {error}")
    return 1 if errores else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lecciones", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ordenes = parser.add_subparsers(dest="orden", required=True)
    ordenes.add_parser("check")
    ordenes.add_parser("mapa")
    ordenes.add_parser("citas")
    ordenes.add_parser("legado")
    evidencia = ordenes.add_parser("evidencia")
    evidencia.add_argument(
        "--db",
        type=Path,
        default=Path(os.environ["NEUROLOGY_DB"]) if os.environ.get("NEUROLOGY_DB") else None,
    )
    nuevo = ordenes.add_parser("nuevo")
    nuevo.add_argument("id")
    proyectar = ordenes.add_parser("proyectar")
    proyectar.add_argument("id")
    proyectar.add_argument("--salida", type=Path, default=SALIDA_PROYECCION)
    args = parser.parse_args(argv)
    if args.orden == "check":
        return _check()
    if args.orden == "mapa":
        return _mapa()
    if args.orden == "nuevo":
        return _nuevo(args.id)
    if args.orden == "proyectar":
        return _proyectar(args.id, args.salida)
    if args.orden == "evidencia":
        return _evidencia(args.db)
    if args.orden == "legado":
        return _legado()
    return _citas()


if __name__ == "__main__":
    sys.exit(main())
