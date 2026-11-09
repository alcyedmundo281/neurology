"""Carga de los módulos clínicos de Neurología y del banco de autoevaluación."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MODULOS_YAML = RAIZ / "assets" / "libro" / "modulos.yaml"


@dataclass(frozen=True)
class CapituloModulo:
    archivo_qmd: str
    titulo: str
    subtitulo: str
    fuentes_repositorio: tuple[str, ...]
    cuerpo_qmd: str


@dataclass(frozen=True)
class PreguntaAutoevaluacion:
    numero: int
    dominio: str
    fuente: str
    enunciado: str
    opciones: tuple[str, ...]
    indice_correcto: int
    justificacion: str


@lru_cache(maxsize=1)
def _cargar_yaml_modulos(ruta: Path = RUTA_MODULOS_YAML) -> dict[str, object]:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ValueError(f"{ruta}: se esperaba un diccionario YAML")
    return datos


def obtener_capitulos_modulos(ruta: Path = RUTA_MODULOS_YAML) -> tuple[CapituloModulo, ...]:
    """Devuelve los capítulos clínicos estructurados de los módulos de neurologia/."""
    datos = _cargar_yaml_modulos(ruta)
    lista_raw = datos.get("capitulos", [])
    if not isinstance(lista_raw, list):
        raise ValueError(f"{ruta}: 'capitulos' debe ser una lista")
    capitulos: list[CapituloModulo] = []
    for item in lista_raw:
        if not isinstance(item, dict):
            continue
        fuentes_raw = item.get("fuentes_repositorio", [])
        fuentes = tuple(str(f) for f in fuentes_raw) if isinstance(fuentes_raw, list) else ()
        capitulos.append(
            CapituloModulo(
                archivo_qmd=str(item["archivo_qmd"]),
                titulo=str(item["titulo"]),
                subtitulo=str(item["subtitulo"]),
                fuentes_repositorio=fuentes,
                cuerpo_qmd=str(item["cuerpo_qmd"]),
            )
        )
    return tuple(capitulos)


def obtener_banco_autoevaluacion(
    ruta: Path = RUTA_MODULOS_YAML,
) -> tuple[PreguntaAutoevaluacion, ...]:
    """Devuelve el banco de casos de autoevaluación integradora."""
    datos = _cargar_yaml_modulos(ruta)
    lista_raw = datos.get("autoevaluacion", [])
    if not isinstance(lista_raw, list):
        raise ValueError(f"{ruta}: 'autoevaluacion' debe ser una lista")
    preguntas: list[PreguntaAutoevaluacion] = []
    for item in lista_raw:
        if not isinstance(item, dict):
            continue
        opciones_raw = item.get("opciones", [])
        opciones = tuple(str(op) for op in opciones_raw) if isinstance(opciones_raw, list) else ()
        preguntas.append(
            PreguntaAutoevaluacion(
                numero=int(item["numero"]),
                dominio=str(item["dominio"]),
                fuente=str(item["fuente"]),
                enunciado=str(item["enunciado"]),
                opciones=opciones,
                indice_correcto=int(item["indice_correcto"]),
                justificacion=str(item["justificacion"]),
            )
        )
    return tuple(preguntas)


def verificar_fuentes_neurologia(raiz: Path = RAIZ) -> list[str]:
    """Verifica que todos los módulos fuente de neurologia/ existan en el repositorio."""
    faltantes: list[str] = []
    for cap in obtener_capitulos_modulos():
        for rel in cap.fuentes_repositorio:
            ruta = raiz / rel
            if not ruta.is_file():
                faltantes.append(rel)
    if not (raiz / "neurologia-autoevaluacion.html").is_file():
        faltantes.append("neurologia-autoevaluacion.html")
    return faltantes
