"""Casos socráticos (ABP dirigido) anclados a la evidencia de medsemiotics-db.

El caso aporta el contexto clínico; la evidencia sigue siendo la de la base. Cada cifra
(LR, sensibilidad, especificidad) llega al caso por un token que se resuelve contra el
artículo derivado de medsemiotics-db, nunca escrita a mano por el autor.
"""

from casos.errores import ErrorDeCaso

__all__ = ["ErrorDeCaso"]
