"""Esquema de ``casos/HM####.yaml``: el caso socrático que da contexto a un artículo.

Estructura de ABP dirigido en cuatro fases, en este orden:

1. ``activacion``: viñeta, conocimientos previos e hipótesis iniciales.
2. ``exploracion``: los hallazgos de la base aparecen como datos del paciente.
3. ``discriminacion``: el estudiante razona con los cocientes documentados.
4. ``decision``: juicio clínico y conducta.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Self

from lecciones.modelo import AGENTES, Autor
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

HmId = Annotated[str, StringConstraints(pattern=r"^HM:\d+$")]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TextoLargo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10)]
Fase = Literal["activacion", "exploracion", "discriminacion", "decision"]
Estado = Literal["borrador", "en_revision", "publicado"]

ORDEN_FASES: dict[str, int] = {
    "activacion": 0,
    "exploracion": 1,
    "discriminacion": 2,
    "decision": 3,
}
ETIQUETA_FASE: dict[str, str] = {
    "activacion": "Activación e hipótesis iniciales",
    "exploracion": "Exploración de hallazgos",
    "discriminacion": "Discriminación con la evidencia",
    "decision": "Juicio clínico y decisión",
}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Dato(_Base):
    etiqueta: Texto
    valor: Texto


class Pregunta(_Base):
    pregunta: TextoLargo
    clave: TextoLargo


class Vineta(_Base):
    titulo: Texto
    texto: TextoLargo
    datos: list[Dato] = Field(default_factory=list)


class Etapa(_Base):
    titulo: Texto
    fase: Fase
    informacion: TextoLargo | None = None
    datos: list[Dato] = Field(default_factory=list)
    hallazgos: list[HmId] = Field(default_factory=list)
    preguntas: list[Pregunta] = Field(min_length=1)

    @model_validator(mode="after")
    def _hallazgos_en_fases_de_evidencia(self) -> Self:
        if self.fase in ("exploracion", "discriminacion") and not self.hallazgos:
            raise ValueError(
                f"la etapa «{self.titulo}» ({self.fase}) debe poner en juego al menos "
                "un hallazgo de medsemiotics-db"
            )
        if len(set(self.hallazgos)) != len(self.hallazgos):
            raise ValueError(f"la etapa «{self.titulo}» repite hallazgos")
        return self


class Omision(_Base):
    hallazgo: HmId
    motivo: TextoLargo


class Cierre(_Base):
    sintesis: TextoLargo
    necesidades_aprendizaje: list[Texto] = Field(min_length=1)


class Autoria(_Base):
    """Autores como en las lecciones (nombre, ORCID, roles CRediT) y un revisor humano."""

    autores: list[Autor] = Field(min_length=1)
    revisor: Texto | None = None

    @model_validator(mode="after")
    def _revisor_humano(self) -> Self:
        if self.revisor is not None and AGENTES.search(self.revisor):
            raise ValueError("revisor: debe ser una persona; el agente nunca es revisor")
        return self


class Revision(_Base):
    fecha: date
    nota: TextoLargo


class Publicacion(_Base):
    fecha: date | None = None
    revisiones: list[Revision] = Field(default_factory=list)

    @property
    def version(self) -> int:
        return 1 + len(self.revisiones)

    @property
    def ultima_fecha(self) -> date | None:
        return self.revisiones[-1].fecha if self.revisiones else self.fecha

    @model_validator(mode="after")
    def _cronologia(self) -> Self:
        if self.revisiones and self.fecha is None:
            raise ValueError("hay revisiones sin fecha de publicación original")
        anterior = self.fecha
        for revision in self.revisiones:
            if anterior is not None and revision.fecha <= anterior:
                raise ValueError(
                    f"la revisión del {revision.fecha} no es posterior a la del {anterior}"
                )
            anterior = revision.fecha
        return self


class Caso(_Base):
    condicion_id: HmId
    estado: Estado
    autoria: Autoria
    publicacion: Publicacion = Field(default_factory=Publicacion)
    nivel: Texto = "Pregrado"
    duracion_min: int = Field(ge=10, le=240)
    objetivos: list[Texto] = Field(min_length=1, max_length=6)
    vineta: Vineta
    etapas: list[Etapa] = Field(min_length=3)
    cierre: Cierre
    omitidos: list[Omision] = Field(default_factory=list)

    @model_validator(mode="after")
    def _secuencia_abp(self) -> Self:
        fases = [etapa.fase for etapa in self.etapas]
        if fases[0] != "activacion" or fases[-1] != "decision":
            raise ValueError("las etapas deben empezar en «activacion» y terminar en «decision»")
        orden = [ORDEN_FASES[fase] for fase in fases]
        if orden != sorted(orden):
            raise ValueError(
                "las fases deben seguir el orden activacion → exploracion → "
                "discriminacion → decision"
            )
        if "discriminacion" not in fases:
            raise ValueError("falta una etapa de «discriminacion» con la evidencia de la base")
        return self

    @model_validator(mode="after")
    def _aprobacion_humana(self) -> Self:
        if self.estado == "publicado":
            if not self.autoria.revisor:
                raise ValueError("un caso publicado requiere un revisor humano nominado")
            if self.publicacion.fecha is None:
                raise ValueError("un caso publicado requiere publicacion.fecha")
        elif self.publicacion.fecha is not None:
            raise ValueError(
                f"un caso en estado «{self.estado}» no puede tener fecha de publicación"
            )
        return self
