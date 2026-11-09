"""Mapa del libro (``lecciones/mapa.yaml``): plan editorial legible por máquina.

El mapa es la fuente del plan; cada lección es la fuente de su contenido y de su estado.
De aquí salen ``mapa-maestro-libro.md`` (generado, versionado y comprobado en los gates),
el esqueleto de cada lección nueva y, en la fase 5, el orden de los capítulos del libro.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from lecciones.fuente import CARPETA, RAIZ, ErrorDeFuente, archivos, leer
from lecciones.modelo import Autor, HmId, Parte, Texto

if TYPE_CHECKING:
    from pathlib import Path

MAPA = CARPETA / "mapa.yaml"
SALIDA = RAIZ / "mapa-maestro-libro.md"
PLANTILLA = RAIZ / "assets" / "plantilla-leccion.qmd"
INDICE_MODULOS = RAIZ / "assets" / "libro" / "modulos-publicados.txt"
URL_PLATAFORMA = "https://powersemiotics.com/medsemiotics/"

ICONOS = {
    "pendiente": "⬜ pendiente",
    "borrador": "✏️ borrador",
    "revisado": "🔎 revisado",
    "publicado": "✅ publicado",
}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Obra(_Base):
    titulo: Texto
    subtitulo: Texto | None = None
    licencia: Literal["CC BY-NC-SA 4.0"]
    legado: Texto
    fuentes_previas: list[Texto] = Field(default_factory=list)
    # Único correo de contacto editorial de la obra (créditos). Nunca el de una persona autora.
    contacto: (
        Annotated[str, StringConstraints(pattern=r"^[\w.+-]+@powersemiotics\.com$")] | None
    ) = None


class ParteMapa(_Base):
    clave: Parte
    titulo: Texto
    autores: list[str] = Field(min_length=1)
    revisor: str
    nota: Texto | None = None


class Autoevaluaciones(_Base):
    """Bancos de preguntas de toda la obra: quién los escribe y quién los revisa."""

    autores: list[str] = Field(min_length=1)
    revisor: str


class FilaMapa(_Base):
    id: Annotated[str, StringConstraints(pattern=r"^leccion-[a-z0-9]+(-[a-z0-9]+)*$")]
    titulo: Texto
    parte: Parte
    orden: int = Field(ge=1)
    fase: Literal[1, 2, 3, 4, 5]
    modulos_html: list[Texto] = Field(default_factory=list)
    legado_paginas: Annotated[str, StringConstraints(pattern=r"^\d+(-\d+)?$")] | None = None
    condiciones: list[HmId] = Field(default_factory=list)
    propuesta: bool = False


class SemanaSilabo(_Base):
    semana: int = Field(ge=1)
    unidad: int = Field(ge=1)
    tema: Texto
    lecciones: list[str] = Field(min_length=1)


class Silabo(_Base):
    """Sílabo vigente: cada semana del curso tiene que estar desarrollada en el libro."""

    asignatura: Texto
    periodo: Texto
    semanas: list[SemanaSilabo] = Field(min_length=1)


class Mapa(_Base):
    obra: Obra
    personas: dict[str, Autor]
    partes: list[ParteMapa] = Field(min_length=1)
    lecciones: list[FilaMapa]
    autoevaluaciones: Autoevaluaciones | None = None
    silabo: Silabo | None = None

    @model_validator(mode="after")
    def _integridad(self) -> Self:
        claves = [p.clave for p in self.partes]
        if len(set(claves)) != len(claves):
            raise ValueError("partes: clave repetida")
        for parte in self.partes:
            for alias in [*parte.autores, parte.revisor]:
                if alias not in self.personas:
                    raise ValueError(f"parte {parte.clave}: persona desconocida «{alias}»")
            if self.personas[parte.revisor].fallecido:
                raise ValueError(f"parte {parte.clave}: el revisor no puede ser el autor fallecido")
        if self.autoevaluaciones is not None:
            banco = self.autoevaluaciones
            for alias in [*banco.autores, banco.revisor]:
                if alias not in self.personas:
                    raise ValueError(f"autoevaluaciones: persona desconocida «{alias}»")
            if self.personas[banco.revisor].fallecido:
                raise ValueError("autoevaluaciones: el revisor no puede ser el autor fallecido")
        repetidos = [i for i, n in Counter(f.id for f in self.lecciones).items() if n > 1]
        if repetidos:
            raise ValueError(f"lecciones: id repetido {repetidos}")
        orden = Counter((f.parte, f.orden) for f in self.lecciones)
        dobles = [k for k, n in orden.items() if n > 1]
        if dobles:
            raise ValueError(f"lecciones: orden repetido en {dobles}")
        for fila in self.lecciones:
            if fila.parte not in claves:
                raise ValueError(f"{fila.id}: parte «{fila.parte}» no declarada")
        if self.silabo is not None:
            ids = {f.id for f in self.lecciones}
            numeros = [s.semana for s in self.silabo.semanas]
            if numeros != sorted(set(numeros)):
                raise ValueError("silabo: semanas repetidas o fuera de orden")
            for s in self.silabo.semanas:
                ajenas = [i for i in s.lecciones if i not in ids]
                if ajenas:
                    raise ValueError(
                        f"silabo: semana {s.semana} cita lecciones fuera del mapa {ajenas}"
                    )
        modulos = Counter(m for f in self.lecciones for m in f.modulos_html)
        compartidos = [m for m, n in modulos.items() if n > 1]
        if compartidos:
            raise ValueError(f"módulos asignados a más de una lección: {compartidos}")
        return self

    def parte(self, clave: str) -> ParteMapa:
        return next(p for p in self.partes if p.clave == clave)

    def fundador(self) -> str | None:
        return next((k for k, p in self.personas.items() if p.rol_obra == "autor-fundador"), None)

    def fila(self, ident: str) -> FilaMapa | None:
        return next((f for f in self.lecciones if f.id == ident), None)


def cargar(ruta: Path = MAPA) -> Mapa:
    if not ruta.is_file():
        raise ErrorDeFuente(f"no existe {ruta.relative_to(RAIZ)}")
    return Mapa.model_validate(yaml.safe_load(ruta.read_text(encoding="utf-8")))


def modulos_publicados(indice: Path = INDICE_MODULOS) -> list[str]:
    """Módulos de neurología enlazados desde su página índice (los que se usan en clase)."""
    if not indice.is_file():
        return []
    return sorted(set(indice.read_text(encoding="utf-8").splitlines()))


def estados(rutas: list[Path] | None = None) -> dict[str, dict[str, Any]]:
    """Frontmatter de cada lección existente, por id (lo ilegible lo informa ``check``)."""
    salida: dict[str, dict[str, Any]] = {}
    for ruta in archivos() if rutas is None else rutas:
        try:
            datos = leer(ruta).datos
        except ErrorDeFuente:
            continue
        if isinstance(datos.get("id"), str):
            salida[datos["id"]] = {**datos, "_archivo": ruta.name}
    return salida


def coherencia(mapa: Mapa, lecciones: dict[str, dict[str, Any]], raiz: Path = RAIZ) -> list[str]:
    errores: list[str] = []
    publicados = modulos_publicados(raiz / INDICE_MODULOS.relative_to(RAIZ))
    for fila in mapa.lecciones:
        for modulo in fila.modulos_html:
            if modulo not in publicados:
                errores.append(f"mapa: {fila.id}: no existe {modulo}")
    asignados = {m for f in mapa.lecciones for m in f.modulos_html}
    for modulo in publicados:
        if modulo not in asignados:
            errores.append(f"mapa: el módulo de clase {modulo} no está asignado a ninguna lección")

    for ident, datos in lecciones.items():
        archivo = datos["_archivo"]
        plan = mapa.fila(ident)
        if plan is None:
            errores.append(f"{archivo}: la lección no figura en lecciones/mapa.yaml")
            continue
        for campo in ("titulo", "parte", "orden"):
            if datos.get(campo) != getattr(plan, campo):
                errores.append(
                    f"{archivo}: {campo} «{datos.get(campo)}» ≠ mapa «{getattr(plan, campo)}»"
                )
        if sorted(datos.get("modulos_html") or []) != sorted(plan.modulos_html):
            errores.append(f"{archivo}: modulos_html no coincide con el mapa")
        faltan = set(plan.condiciones) - set(datos.get("condiciones") or [])
        if faltan:
            errores.append(f"{archivo}: faltan condiciones del mapa {sorted(faltan)}")
        legado = datos.get("legado") or {}
        if (legado.get("paginas") if isinstance(legado, dict) else None) != plan.legado_paginas:
            errores.append(f"{archivo}: legado.paginas no coincide con el mapa")
        nombres = {a.get("nombre") for a in datos.get("autores") or [] if isinstance(a, dict)}
        fundador = mapa.fundador()
        if (
            plan.legado_paginas
            and fundador is not None
            and mapa.personas[fundador].nombre not in nombres
        ):
            errores.append(f"{archivo}: una lección con legado lleva al autor fundador")
        for alias in mapa.parte(plan.parte).autores:
            if mapa.personas[alias].nombre not in nombres:
                nombre = mapa.personas[alias].nombre
                errores.append(f"{archivo}: falta el autor de la parte «{nombre}»")
    return errores


def _celda_fuente(fila: FilaMapa) -> str:
    partes: list[str] = []
    if fila.legado_paginas:
        partes.append(f"1993, pp. {fila.legado_paginas}")
    partes += [f"`{m.removeprefix('neurologia/')}`" for m in fila.modulos_html]
    partes += [f"db `{c}`" for c in fila.condiciones]
    return " · ".join(partes) or "nueva"


def renderizar(mapa: Mapa, lecciones: dict[str, dict[str, Any]], raiz: Path = RAIZ) -> str:
    total = Counter(lecciones.get(f.id, {}).get("estado", "pendiente") for f in mapa.lecciones)
    lineas = [
        "# Mapa maestro del libro",
        "",
        "<!-- GENERADO desde lecciones/mapa.yaml y lecciones/*.qmd con "
        "`python -m lecciones mapa`. No editar a mano. -->",
        "",
        f"**Obra:** {mapa.obra.titulo}  ",
        f"**Legado:** {mapa.obra.legado}  ",
        f"**Licencia:** {mapa.obra.licencia} (lecciones y libro)",
        "",
        "Cada fila es una lección: una fuente única (`lecciones/<id>.qmd`) de la que salen el "
        "artículo del blog y el capítulo del libro. Todo el texto se reconstruye desde cero; "
        "los módulos de clase y la obra de 1993 son fuentes, no texto que se copia. El estado "
        "se lee de cada lección. Contrato: `docs/adr/ADR-001-arquitectura-libro.md`.",
        "",
        "**Estado:** "
        + " · ".join(f"{ICONOS[k]}: {total.get(k, 0)}" for k in ICONOS)
        + f" · total {len(mapa.lecciones)}",
        "",
        "**Fases:** 1 piloto · 2 módulos de clase · 3 neuropediatría · 4 neuroftalmología · "
        "5 libro. «(propuesta)» marca una agrupación de módulos pendiente de decisión.",
        "",
    ]
    for numero, parte in enumerate(mapa.partes, 1):
        autores = ", ".join(
            mapa.personas[a].nombre + (" †" if mapa.personas[a].fallecido else "")
            for a in parte.autores
        )
        lineas += [
            f"## {numero}. {parte.titulo}",
            "",
            f"Autores: {autores} · Revisión: {mapa.personas[parte.revisor].nombre}",
            "",
        ]
        if parte.nota:
            lineas += [f"*{parte.nota}*", ""]
        filas = sorted((f for f in mapa.lecciones if f.parte == parte.clave), key=lambda f: f.orden)
        if not filas:
            lineas += ["*Sin lecciones planificadas todavía.*", ""]
            continue
        lineas += ["| # | Lección | Fase | Fuentes | Estado |", "|:-|:-|:-|:-|:-|"]
        for f in filas:
            estado = ICONOS.get(str(lecciones.get(f.id, {}).get("estado", "pendiente")), "?")
            titulo = f.titulo + (" *(propuesta)*" if f.propuesta else "")
            lineas.append(
                f"| {f.orden} | {titulo}<br>`{f.id}` | {f.fase} | {_celda_fuente(f)} | {estado} |"
            )
        lineas.append("")

    if mapa.autoevaluaciones is not None:
        banco = mapa.autoevaluaciones
        lineas += [
            "## Autoevaluaciones de toda la obra",
            "",
            "Autores: "
            + ", ".join(mapa.personas[a].nombre for a in banco.autores)
            + f" · Revisión: {mapa.personas[banco.revisor].nombre}",
            "",
        ]

    if mapa.silabo is not None:
        titulos = {f.id: f.titulo for f in mapa.lecciones}
        lineas += [
            "## Cobertura del sílabo",
            "",
            f"{mapa.silabo.asignatura} · período {mapa.silabo.periodo}. Cada semana del curso "
            "tiene que estar desarrollada en el libro.",
            "",
            "| Semana | Unidad | Tema | Lecciones | Estado |",
            "|:-|:-|:-|:-|:-|",
        ]
        for s in mapa.silabo.semanas:
            nombres = "<br>".join(titulos[i] for i in s.lecciones)
            estados_semana = "<br>".join(
                ICONOS.get(str(lecciones.get(i, {}).get("estado", "pendiente")), "?")
                for i in s.lecciones
            )
            lineas.append(f"| {s.semana} | {s.unidad} | {s.tema} | {nombres} | {estados_semana} |")
        lineas.append("")

    asignacion = {m: f for f in mapa.lecciones for m in f.modulos_html}
    publicados = modulos_publicados(raiz / INDICE_MODULOS.relative_to(RAIZ))
    lineas += [
        "## Cobertura de los módulos de clase",
        "",
        f"{len(publicados)} módulos del [índice de Medsemiotics]({URL_PLATAFORMA}neurologia.html).",
        "",
        "| Módulo | Lección |",
        "|:-|:-|",
    ]
    for modulo in publicados:
        fila = asignacion.get(modulo)
        lineas.append(
            f"| [{modulo}]({URL_PLATAFORMA}{modulo}) | "
            f"{fila.titulo if fila else '**sin asignar**'} |"
        )
    lineas.append("")
    return "\n".join(lineas)


def esqueleto(mapa: Mapa, ident: str) -> str:
    """Lección nueva en borrador, con todo lo que el mapa ya sabe de ella."""
    fila = mapa.fila(ident)
    if fila is None:
        raise ErrorDeFuente(f"{ident} no figura en lecciones/mapa.yaml")
    parte = mapa.parte(fila.parte)
    alias = list(parte.autores)
    fundador = mapa.fundador()
    if fila.legado_paginas and fundador is not None and fundador not in alias:
        alias.insert(0, fundador)
    pendiente = "PENDIENTE de redacción."
    datos: dict[str, Any] = {
        "id": fila.id,
        "tipo": "leccion",
        "titulo": fila.titulo,
        "parte": fila.parte,
        "orden": fila.orden,
        "estado": "borrador",
        "fecha_revision": None,
        "revisor": None,
        "autores": [
            mapa.personas[a].model_dump(exclude_defaults=True, exclude_none=True) for a in alias
        ],
    }
    # Declaración honesta por defecto: así se crean hoy las lecciones. El autor la corrige.
    datos["uso_ia"] = ["busqueda-bibliografica", "redaccion-borrador"]
    if fila.legado_paginas:
        datos["uso_ia"].insert(0, "transcripcion")
        datos["legado"] = {"obra": mapa.obra.legado, "paginas": fila.legado_paginas}
    datos |= {
        "pregunta_clinica": pendiente,
        "abstract": pendiente,
        "dialogo_clinico": pendiente,
        "indispensable": [pendiente],
        "limites": [pendiente],
        "condiciones": list(fila.condiciones),
        "conceptos": [],
        "refs": [],
        "medios": [],
        "modulos_html": list(fila.modulos_html),
    }
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    cuerpo = plantilla.split("\n---\n", 2)[-1]
    if not fila.legado_paginas:
        cuerpo = re.sub(r"(?ms)^::: \{\.legado\}.*?^:::\s*$\n?", "", cuerpo)
    encabezado = yaml.safe_dump(datos, allow_unicode=True, sort_keys=False, width=100)
    return f"---\n{encabezado}---\n{cuerpo}"
