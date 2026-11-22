"""Integridad de las fichas de evidencia frente a medsemiotics-db en su revisión fijada.

``lecciones check`` comprueba que los tokens resuelvan contra las fichas (``posts/`` y
``lecciones/evidencia/``), pero no que las fichas digan lo que dice la base: una cifra editada a
mano en una ficha llegaría al libro. Aquí se reconstruye cada ficha desde la base:

- cada archivo de ``fuente.archivos`` tiene en la revisión declarada el SHA-256 registrado;
- ``evidencia`` es idéntica a los ``signos`` de la condición en esa revisión;
- el nombre de cada hallazgo (encabezado ``### Nombre (HM:####)``, que usa el token
  ``hallazgo``) es el ``termino`` del concepto en esa revisión;
- las cifras de ``grounding`` son las del signo principal.

Necesita una copia git completa de medsemiotics-db (no un checkout de la revisión: se lee con
``git show <revisión>:<ruta>``). Sin red ni escritura.
"""

from __future__ import annotations

import hashlib
import subprocess
from typing import TYPE_CHECKING, Any

import yaml
from casos.articulo import _dividir, leer_articulo
from casos.errores import ErrorDeCaso

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path


def lector_git(db: Path) -> Callable[[str, str], str | None]:
    """(revisión, ruta) → texto del archivo en esa revisión, o None si no existe."""

    def leer(revision: str, ruta: str) -> str | None:
        r = subprocess.run(
            ["git", "-C", str(db), "show", f"{revision}:{ruta}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        return r.stdout if r.returncode == 0 else None

    return leer


def _sha(texto: str) -> str:
    # Igual que tools/generate_topic.py de medsemiotics: fin de línea LF antes de resumir.
    return hashlib.sha256(texto.replace("\r\n", "\n").encode()).hexdigest()


def problemas_de_ficha(ruta: Path, leer: Callable[[str, str], str | None]) -> list[str]:
    nombre = ruta.name
    try:
        datos, _ = _dividir(ruta.read_text(encoding="utf-8"), ruta)
        articulo = leer_articulo(ruta)
    except ErrorDeCaso as exc:
        return [f"{nombre}: {exc}"]
    fuente: dict[str, Any] = datos.get("fuente") or {}
    revision = str(fuente.get("revision") or "")
    archivos: dict[str, str] = fuente.get("archivos") or {}
    condicion = fuente.get("condicion")
    if not revision or not archivos or condicion not in archivos:
        return [f"{nombre}: fuente sin revisión, sin archivos o sin la condición entre ellos"]

    problemas: list[str] = []
    contenidos: dict[str, Any] = {}
    for ruta_db, esperado in archivos.items():
        texto = leer(revision, ruta_db)
        if texto is None:
            problemas.append(f"{nombre}: {ruta_db} no existe en medsemiotics-db@{revision[:7]}")
            continue
        if _sha(texto) != esperado:
            problemas.append(f"{nombre}: {ruta_db} no coincide con su SHA-256 registrado")
        contenidos[ruta_db] = yaml.safe_load(texto)
    if problemas:
        return problemas

    signos = (contenidos[condicion] or {}).get("signos") or []
    if datos.get("evidencia") != signos:
        problemas.append(
            f"{nombre}: «evidencia» difiere de los signos de {condicion} en "
            f"medsemiotics-db@{revision[:7]}: la ficha fue editada a mano; regenérela"
        )

    terminos = {
        c.get("id"): c.get("termino")
        for c in contenidos.values()
        if isinstance(c, dict) and c.get("tipo") == "concepto"
    }
    for concepto, nombre_hallazgo in articulo.nombres.items():
        if concepto in terminos and terminos[concepto] != nombre_hallazgo:
            problemas.append(
                f"{nombre}: el hallazgo {concepto} se llama «{nombre_hallazgo}» en la ficha y "
                f"«{terminos[concepto]}» en la base"
            )

    grounding = datos.get("grounding") or {}
    principal = next((s for s in signos if s.get("concepto") == grounding.get("concepto_id")), None)
    if principal is not None:
        esperado_g = {
            "lr_positivo": (principal.get("lr_positivo") or {}).get("valor"),
            "lr_negativo": (principal.get("lr_negativo") or {}).get("valor"),
            "sensibilidad": principal.get("sensibilidad"),
            "especificidad": principal.get("especificidad"),
        }
        for campo, valor in esperado_g.items():
            if grounding.get(campo) != valor:
                problemas.append(
                    f"{nombre}: grounding.{campo} = {grounding.get(campo)!r}, "
                    f"la base dice {valor!r}"
                )
    return problemas


def problemas_de_fichas(rutas: Iterable[Path], leer: Callable[[str, str], str | None]) -> list[str]:
    return [p for ruta in rutas for p in problemas_de_ficha(ruta, leer)]
