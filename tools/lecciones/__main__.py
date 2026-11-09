"""CLI: ``python -m lecciones <orden>``.

- ``check``: contrato de todas las lecciones, coherencia con ``lecciones/mapa.yaml`` y
  ``mapa-maestro-libro.md`` al día, y que todo token de evidencia resuelva contra ``posts/`` y
  ``lecciones/evidencia/``, de una sola revisión de la db (sin red).
- ``mapa``: regenera ``mapa-maestro-libro.md`` desde el mapa y el estado de las lecciones.
- ``nuevo <id>``: crea ``lecciones/<id>.qmd`` en borrador desde su fila del mapa.
- ``proyectar <id>``: escribe la lección con sus tokens resueltos (``build/lecciones/<id>.qmd``
  y ``refs.bib``), lista para ``quarto render``; aborta si un token no resuelve.
- ``citas``: verifica ``lecciones/refs.bib`` contra PubMed y Crossref (requiere red).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from casos.errores import ErrorDeCaso
from lecciones import mapa as mapa_libro
from lecciones.citas import verificar
from lecciones.evidencia import cargar_articulos
from lecciones.fuente import CARPETA, RAIZ, ErrorDeFuente, archivos, leer, leer_bib
from lecciones.proyectar import escribir_proyeccion, problemas_de_resolucion
from lecciones.validacion import validar_todo


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


def _check() -> int:
    rutas = archivos()
    resultado = validar_todo(rutas)
    errores = list(resultado.errores)
    errores += _problemas_de_tokens(rutas)
    mapa = _cargar_mapa()
    if mapa is None:
        return 1
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
    for aviso in informe.avisos:
        print(f"⚠ {aviso}")
    for linea in informe.discrepancias:
        print(f"✗ {linea}")
    for linea in informe.incompletas:
        print(f"… {linea}")
    print(
        f"refs.bib: {len(informe.verificadas)}/{len(bib)} verificadas en PubMed y Crossref"
        + (" (INCOMPLETA)" if informe.incompletas else "")
    )
    return informe.codigo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lecciones", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ordenes = parser.add_subparsers(dest="orden", required=True)
    ordenes.add_parser("check")
    ordenes.add_parser("mapa")
    ordenes.add_parser("citas")
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
    return _citas()


if __name__ == "__main__":
    sys.exit(main())
