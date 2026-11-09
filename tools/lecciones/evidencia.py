"""Evidencia de medsemiotics-db que las lecciones pueden citar, a una sola revisión fijada.

Dos orígenes, ambos escritos por ``tools/generate_topic.py`` desde la misma revisión de la db:

- ``posts/``: artículos publicados en el blog.
- ``lecciones/evidencia/``: la evidencia de las condiciones excluidas de la publicación
  (``tools/topics-excluidos.yaml``). La exclusión solo afecta al blog, no a las lecciones.

Nunca se lee la rama viva de la db: libro y blog citan exactamente los mismos números. Si los
archivos no comparten revisión, o una condición está en los dos orígenes, es un error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from casos.articulo import leer_articulos
from casos.errores import ErrorDeCaso
from lecciones.fuente import RAIZ

if TYPE_CHECKING:
    from pathlib import Path

    from casos.articulo import Articulo


def cargar_articulos(raiz: Path = RAIZ) -> dict[str, Articulo]:
    """Artículos por condición, publicados y reservados, de una única revisión de la db."""
    publicados = leer_articulos(raiz / "posts") if (raiz / "posts").is_dir() else {}
    carpeta = raiz / "lecciones" / "evidencia"
    reservados = leer_articulos(carpeta) if carpeta.is_dir() else {}
    repetidas = sorted(set(publicados) & set(reservados))
    if repetidas:
        raise ErrorDeCaso(
            f"condición en posts/ y en lecciones/evidencia/ a la vez: {repetidas}; "
            "una publicada ya no es reservada."
        )
    todos = {**publicados, **reservados}
    revisiones = sorted({a.revision_fuente for a in todos.values()})
    if len(revisiones) > 1:
        raise ErrorDeCaso(
            "la evidencia viene de varias revisiones de medsemiotics-db "
            f"({', '.join(r[:7] for r in revisiones)}): actualice juntas las fichas de evidencia"
        )
    return todos
