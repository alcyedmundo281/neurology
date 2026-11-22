"""Citas literales de la obra de 1993 (bloques ``::: {.legado}``) y su cotejo humano.

La transcripción de 1993 es privada y no está en el repositorio, así que la máquina no puede
comparar una cita con el impreso. Lo que sí puede hacer es:

- exigir que cada bloque tenga una cita «…» y una atribución con su página, dentro del rango de
  páginas que la lección declara en ``legado.paginas``;
- registrar el cotejo humano: ``lecciones/legado-cotejo.yaml`` guarda, por cita, el SHA-256 de su
  texto, quién la cotejó contra el impreso y cuándo. Si la cita cambia, su resumen ya no coincide
  y el cotejo deja de valer. Una lección revisada o publicada no sale con citas sin cotejar.

``python -m lecciones legado`` lista las citas con su resumen y su estado de cotejo.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from lecciones.fuente import CARPETA, ErrorDeFuente
from lecciones.modelo import AGENTES, Texto

if TYPE_CHECKING:
    from pathlib import Path

REGISTRO = CARPETA / "legado-cotejo.yaml"
BLOQUE_LEGADO = re.compile(r"(?ms)^:::\s*\{\.legado\}\s*$(?P<dentro>.*?)^:::\s*$")
CITA = re.compile(r"«(?P<texto>.+?)»", re.S)
ATRIBUCION = re.compile(
    r"^—\s*A\.\s*Torres Catefort,\s*\*Neurología Pediátrica\*,\s*"
    r"(?P<p>pp?)\.\s*(?P<paginas>\d+(?:-\d+)?)\s*$",
    re.M,
)


@dataclass(frozen=True)
class CitaLegado:
    texto: str
    paginas: str | None
    sha: str


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def resumen(texto: str) -> str:
    return hashlib.sha256(_normalizar(texto).encode()).hexdigest()


def _rango(paginas: str) -> set[int]:
    salida: set[int] = set()
    for tramo in paginas.split(","):
        a, _, b = tramo.strip().partition("-")
        salida |= set(range(int(a), int(b or a) + 1))
    return salida


def citas(cuerpo: str) -> tuple[list[CitaLegado], list[str]]:
    """Las citas de los bloques legado y los problemas de forma de cada bloque."""
    encontradas: list[CitaLegado] = []
    problemas: list[str] = []
    for n, m in enumerate(BLOQUE_LEGADO.finditer(cuerpo), 1):
        dentro = m["dentro"]
        textos = CITA.findall(dentro)
        atribucion = ATRIBUCION.search(dentro)
        if len(textos) != 1:
            problemas.append(f"bloque legado {n}: debe tener exactamente una cita «…»")
        if atribucion is None:
            problemas.append(
                f"bloque legado {n}: falta la atribución "
                "«— A. Torres Catefort, *Neurología Pediátrica*, p. N»"
            )
        elif (atribucion["p"] == "pp") != ("-" in atribucion["paginas"]):
            problemas.append(f"bloque legado {n}: «p.» es para una página y «pp.» para un rango")
        for texto in textos[:1]:
            paginas = atribucion["paginas"] if atribucion else None
            encontradas.append(CitaLegado(_normalizar(texto), paginas, resumen(texto)))
    return encontradas, problemas


def problemas_de_paginas(encontradas: list[CitaLegado], declaradas: str | None) -> list[str]:
    if declaradas is None:
        return ["tiene bloques legado pero no declara «legado.paginas»"] if encontradas else []
    rango = _rango(declaradas)
    return [
        f"cita legado en p. {c.paginas}, fuera de las páginas declaradas ({declaradas})"
        for c in encontradas
        if c.paginas is not None and not _rango(c.paginas) <= rango
    ]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Cotejo(_Base):
    leccion: Annotated[str, StringConstraints(pattern=r"^leccion-[a-z0-9-]+$")]
    paginas: Texto
    sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    cotejado_por: Texto
    fecha: date


class Registro(_Base):
    cotejos: list[Cotejo] = Field(default_factory=list)


def cargar_registro(ruta: Path = REGISTRO) -> Registro:
    if not ruta.is_file():
        return Registro()
    try:
        return Registro.model_validate(yaml.safe_load(ruta.read_text(encoding="utf-8")) or {})
    except Exception as exc:  # pydantic o YAML: el registro ilegible bloquea
        raise ErrorDeFuente(f"{ruta.name}: {exc}") from exc


def problemas_de_cotejo(
    leccion: str,
    encontradas: list[CitaLegado],
    registro: Registro,
    personas_vivas: set[str],
) -> list[str]:
    """Citas sin cotejo válido. El cotejador es una persona viva del mapa, nunca un agente."""
    problemas: list[str] = []
    propios = {c.sha256: c for c in registro.cotejos if c.leccion == leccion}
    for cita in encontradas:
        cotejo = propios.get(cita.sha)
        if cotejo is None:
            problemas.append(
                f"cita legado de p. {cita.paginas} sin cotejo contra el impreso "
                f"(sha256 {cita.sha[:12]}…; véase python -m lecciones legado)"
            )
            continue
        if cotejo.paginas != cita.paginas:
            problemas.append(
                f"cotejo de {cita.sha[:12]}…: páginas {cotejo.paginas} ≠ {cita.paginas}"
            )
        if AGENTES.search(cotejo.cotejado_por) or cotejo.cotejado_por not in personas_vivas:
            problemas.append(
                f"cotejo de {cita.sha[:12]}…: «{cotejo.cotejado_por}» "
                "no es una persona viva del mapa"
            )
        if cotejo.fecha > date.today():
            problemas.append(f"cotejo de {cita.sha[:12]}…: fecha futura")
    return problemas


def huerfanos(registro: Registro, vigentes: dict[str, set[str]]) -> list[str]:
    """Cotejos cuya cita ya no existe: el texto cambió después de cotejarse."""
    return [
        f"legado-cotejo.yaml: el cotejo {c.sha256[:12]}… de {c.leccion} (p. {c.paginas}) no "
        "corresponde a ninguna cita actual; la cita cambió tras el cotejo"
        for c in registro.cotejos
        if c.sha256 not in vigentes.get(c.leccion, set())
    ]
