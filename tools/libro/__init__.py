"""Generador del libro impreso de neurología (Quarto + LuaLaTeX).

Construye el proyecto Quarto en ``build/quarto/`` con formato de catálogo KDP e IngramSpark
(6,69 × 9,61 pulgadas = 170 × 244 mm), compila el PDF con ``quarto render`` + ``lualatex`` y
verifica las dimensiones de página y metadatos con ``pdfinfo``.
"""

from __future__ import annotations

ANCHO_MM: int = 170
ALTO_MM: int = 244
ANCHO_PULGADAS: float = 6.69
ALTO_PULGADAS: float = 9.61
# 170 mm = 481.8898 pt; 244 mm = 691.6535 pt (72 pt/in, 25.4 mm/in)
ANCHO_PT: float = 481.89
ALTO_PT: float = 691.65
TOLERANCIA_PT: float = 1.5

CONDICIONES_NEUROLOGIA: tuple[str, ...] = (
    "HM:6004",
    "HM:6015",
    "HM:6023",
    "HM:6038",
)

__all__ = [
    "ALTO_MM",
    "ALTO_PT",
    "ALTO_PULGADAS",
    "ANCHO_MM",
    "ANCHO_PT",
    "ANCHO_PULGADAS",
    "CONDICIONES_NEUROLOGIA",
    "TOLERANCIA_PT",
]
