"""Esquema del frontmatter de ``lecciones/<id>.qmd``."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

HmId = Annotated[str, StringConstraints(pattern=r"^HM:\d+$")]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TextoLargo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=20)]
ClaveBib = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_:\-]*$")]

Estado = Literal["borrador", "revisado", "publicado"]
Parte = Literal["fundamentos", "neonato", "lactante-nino", "neuroftalmologia", "adulto"]
RolObra = Literal["autor-fundador", "autor", "coordinacion-editorial", "autor-autoevaluaciones"]
# Etapas en que intervino la IA en una lección (lecciones/AI-USE.md). Lista vacía: no intervino.
UsoIA = Literal[
    "transcripcion",
    "busqueda-bibliografica",
    "redaccion-borrador",
    "revision-estilo",
    "codigo",
]

# Taxonomía CRediT (NISO Z39.104-2022), en las claves en español que usa biosemiotics.
CreditRol = Literal[
    "conceptualizacion",
    "curacion-de-datos",
    "analisis-formal",
    "adquisicion-de-fondos",
    "investigacion",
    "metodologia",
    "administracion-del-proyecto",
    "recursos",
    "software",
    "supervision",
    "validacion",
    "visualizacion",
    "redaccion",
    "revision-edicion",
]

# Roles que un autor fallecido no puede ejercer sobre la edición nueva.
ROLES_SOLO_VIVOS: frozenset[str] = frozenset(
    {"revision-edicion", "supervision", "validacion", "administracion-del-proyecto"}
)

# Un revisor es una persona nominada. Nombres de agentes o modelos no cuentan.
AGENTES = re.compile(r"\b(claude|codex|copilot|gpt|chatgpt|gemini|llm|ia|ai|agente)\b", re.I)

ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
COMMONS = re.compile(r"^https://commons\.wikimedia\.org/wiki/File:.+")


def orcid_valido(orcid: str) -> bool:
    """Formato y dígito de control ISO 7064 MOD 11-2, como lo calcula ORCID."""
    if not ORCID.match(orcid):
        return False
    digitos = orcid.replace("-", "")
    total = 0
    for caracter in digitos[:-1]:
        total = (total + int(caracter)) * 2
    resto = (12 - total % 11) % 11
    control = "X" if resto == 10 else str(resto)
    return digitos[-1] == control


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Autor(_Base):
    nombre: Texto
    orcid: str | None = None
    afiliacion: Texto | None = None
    # Forma con la que la persona firma en la bibliografía (p. ej. «Alcy R. Torres», PubMed:
    # «Torres AR»): se usa en la línea de revisión y en las citas. La portada usa `nombre`.
    nombre_bibliografico: Texto | None = None
    rol_obra: RolObra = "autor"
    fallecido: bool = False
    # Fechas de vida (ISO) de quien las lleva en un paratexto (la dedicatoria). No viajan a los
    # JSON derivados de los casos.
    nacimiento: date | None = Field(default=None, exclude=True)
    fallecimiento: date | None = Field(default=None, exclude=True)
    # Concordancia de género de su función en créditos («autora»): lo dice el mapa, no se deduce
    # del nombre.
    femenino: bool = Field(default=False, exclude=True)
    credit: list[CreditRol] = Field(min_length=1)

    @model_validator(mode="after")
    def _coherencia(self) -> Self:
        if self.orcid is not None and not orcid_valido(self.orcid):
            raise ValueError(f"ORCID inválido para {self.nombre}: {self.orcid}")
        if self.fallecimiento is not None:
            if not self.fallecido:
                raise ValueError(f"{self.nombre}: tiene fecha de fallecimiento pero no fallecido")
            if self.nacimiento is not None and self.nacimiento >= self.fallecimiento:
                raise ValueError(f"{self.nombre}: nace después de fallecer")
        if self.fallecido:
            prohibidos = sorted(ROLES_SOLO_VIVOS.intersection(self.credit))
            if prohibidos:
                raise ValueError(
                    f"{self.nombre} (fallecido) no puede ejercer en esta edición: "
                    + ", ".join(prohibidos)
                )
        return self


class Legado(_Base):
    """De dónde viene, en la obra de 1993, lo que esta lección conserva o actualiza."""

    obra: Texto
    paginas: Annotated[str, StringConstraints(pattern=r"^\d+(-\d+)?(,\s*\d+(-\d+)?)*$")]


class Medio(_Base):
    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]*$")]
    tipo: Literal["imagen"]
    archivo_local: Texto
    origen: Literal["commons", "ilustracion-original"]
    pie: Texto
    licencia: Texto
    credito: Texto
    fuente_url: str | None = None
    autor_ilustracion: Texto | None = None

    @model_validator(mode="after")
    def _procedencia(self) -> Self:
        if self.origen == "commons":
            if self.fuente_url is None or not COMMONS.match(self.fuente_url):
                raise ValueError(
                    f"medio {self.id}: la fuente debe ser una página File: de Wikimedia Commons"
                )
        elif self.autor_ilustracion is None:
            raise ValueError(
                f"medio {self.id}: una ilustración original declara la persona que la hizo"
            )
        return self


class Leccion(_Base):
    id: Annotated[str, StringConstraints(pattern=r"^leccion-[a-z0-9]+(-[a-z0-9]+)*$")]
    tipo: Literal["leccion"]
    titulo: Texto
    subtitulo: Texto | None = None
    parte: Parte
    orden: int = Field(ge=1)
    estado: Estado
    fecha_revision: date | None = None
    revisor: Texto | None = None
    autores: list[Autor] = Field(min_length=1)
    uso_ia: list[UsoIA]
    legado: Legado | None = None
    pregunta_clinica: TextoLargo
    abstract: TextoLargo
    dialogo_clinico: TextoLargo
    indispensable: list[Texto] = Field(min_length=1, max_length=5)
    limites: list[Texto] = Field(min_length=1)
    condiciones: list[HmId] = Field(default_factory=list)
    conceptos: list[HmId] = Field(default_factory=list)
    refs: list[ClaveBib] = Field(default_factory=list)
    medios: list[Medio] = Field(default_factory=list)
    modulos_html: list[Texto] = Field(default_factory=list)

    @model_validator(mode="after")
    def _contrato(self) -> Self:
        palabras = len(self.abstract.split())
        if not 40 <= palabras <= 80:
            raise ValueError(f"abstract: debe tener entre 40 y 80 palabras (tiene {palabras})")
        if self.estado != "borrador":
            if self.revisor is None:
                raise ValueError(f"estado {self.estado}: requiere un revisor nominado")
            if AGENTES.search(self.revisor):
                raise ValueError("revisor: debe ser una persona; el agente nunca es revisor")
            if self.fecha_revision is None:
                raise ValueError(f"estado {self.estado}: requiere fecha_revision")
        if any(a.rol_obra == "autor-fundador" for a in self.autores) and self.legado is None:
            raise ValueError("una lección con autor fundador declara su procedencia en «legado»")
        for campo in ("condiciones", "conceptos", "refs", "uso_ia"):
            valores: list[str] = getattr(self, campo)
            if len(set(valores)) != len(valores):
                raise ValueError(f"{campo}: hay valores repetidos")
        return self
