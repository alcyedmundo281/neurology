"""Tokens de evidencia: la única vía por la que una cifra de la base entra en el texto del caso.

Sintaxis: ``{{tipo HM:####}}``. Tipos:

- ``lr+`` / ``lr-``: cociente de verosimilitud positivo o negativo, con IC 95 % o rango.
- ``sens`` / ``esp``: sensibilidad o especificidad registradas.
- ``hallazgo``: nombre del hallazgo.
- ``estado``: estado del LR (medido, no medido, no medible, sin efecto).

Si la base mide un hallazgo varias veces, ``{{lr+ HM:####@2}}`` cita solo la segunda
medición; sin índice se citan todas, etiquetadas por su referencia si vienen de fuentes
distintas y por su población si comparten fuente.

Si la medición tiene ``tramos`` (cortes de un hallazgo graduado, o la misma prueba evaluada
contra varias definiciones de la condición), ``{{lr+ HM:3012#2}}`` cita el segundo tramo con
su umbral. Con varias mediciones, el tramo exige elegir antes la medición:
``{{lr+ HM:3004@1#2}}``. Los tokens ``hallazgo`` y ``estado`` no admiten tramo.

Fuera de los tokens, el texto no puede escribir cocientes, sensibilidades, IC ni
identificadores: así una corrección en medsemiotics-db se propaga sola al caso.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from casos.errores import ErrorDeCaso

if TYPE_CHECKING:
    from collections.abc import Collection

    from casos.articulo import Articulo

TOKEN = re.compile(
    r"\{\{\s*(?P<tipo>[a-z+\-]+)\s+(?P<id>HM:\d+)(?:@(?P<n>\d+))?(?:#(?P<t>\d+))?\s*\}\}"
)
LLAVES = re.compile(r"\{\{.*?\}\}|\{\{|\}\}")
TIPOS = frozenset({"lr+", "lr-", "sens", "esp", "hallazgo", "estado"})

ESTADOS = {
    "medido": "LR medido",
    "no_medido": "LR no medido",
    "no_medible": "LR no medible",
    "sin_efecto": "sin efecto discriminativo",
}
ROLES = {
    "manifestacion": "Manifestación",
    "prueba_sensible": "Prueba sensible",
    "prueba_especifica": "Prueba específica",
    "apoyo": "Apoyo diagnóstico",
    "imagen": "Imagen",
    "bandera_roja": "Signo de alarma",
}

# Cifras de rendimiento diagnóstico escritas a mano. La lista es deliberadamente amplia:
# un falso positivo se resuelve con un token; un falso negativo publica una cifra huérfana.
PROHIBIDOS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bLR\s*[+\-−]?\s*(?:positivo|negativo)?\s*(?:de|=|:|≈|~)?\s*\d", re.I),
        "cociente de verosimilitud escrito a mano; use {{lr+ HM:…}} o {{lr- HM:…}}",
    ),
    (
        re.compile(
            r"(?:cocientes? de (?:verosimilitud|probabilidad)|likelihood ratios?)"
            r"[^.\n]{0,30}?\d",
            re.I,
        ),
        "cociente de verosimilitud escrito a mano; use {{lr+ HM:…}} o {{lr- HM:…}}",
    ),
    (
        re.compile(r"\b(?:sensibilidad|especificidad)\b[^.\n]{0,25}?\d", re.I),
        "sensibilidad o especificidad escrita a mano; use {{sens HM:…}} o {{esp HM:…}}",
    ),
    (
        re.compile(r"\b(?:VPP|VPN|valores? predictivos?)\b[^.\n]{0,25}?\d", re.I),
        "valor predictivo escrito a mano: la base no lo registra",
    ),
    (re.compile(r"\bIC\s*(?:del?\s*)?95", re.I), "intervalo de confianza escrito a mano"),
    (re.compile(r"\bpmid\b", re.I), "referencia escrita a mano: se deriva de la evidencia"),
    (re.compile(r"\bHM:\d+"), "identificador fuera de token; use {{hallazgo HM:…}}"),
)


def _numero(valor: Any) -> bool:
    return isinstance(valor, int | float) and not isinstance(valor, bool)


def _cociente(etiqueta: str, bloque: Any, concepto: str) -> str:
    if not isinstance(bloque, dict):
        raise ErrorDeCaso(f"{concepto}: la base no registra {etiqueta}.")
    ic95 = bloque.get("ic95")
    rango = bloque.get("rango")
    if _numero(bloque.get("valor")):
        texto = f"{etiqueta} {bloque['valor']}"
        if isinstance(ic95, list) and len(ic95) == 2:
            texto += f" (IC 95 %: {ic95[0]}–{ic95[1]})"
    elif isinstance(rango, list) and len(rango) == 2:
        texto = (
            f"{etiqueta} entre {rango[0]} y {rango[1]} "
            "(rango entre estudios, sin estimación puntual)"
        )
    else:
        raise ErrorDeCaso(f"{concepto}: {etiqueta} sin valor ni rango en la base.")
    return texto + _condiciones(bloque)


def _condiciones(bloque: dict[str, Any], tramo: bool = False) -> str:
    """Contra qué se midió la cifra: el umbral del hallazgo, la definición de la condición
    (``umbral_condicion``) o, en un tramo, su población. Sin esto, dos cifras de la misma prueba
    parecen intercambiables cuando responden a preguntas distintas. La población de una
    medición no se repite en cada cifra: la ficha y los tokens sin ``@n`` ya la muestran."""
    texto = ""
    if bloque.get("umbral"):
        texto += f", con umbral «{bloque['umbral']}»"
    if bloque.get("umbral_condicion"):
        texto += f", para el diagnóstico «{bloque['umbral_condicion']}»"
    if tramo and bloque.get("poblacion"):
        texto += f", en «{bloque['poblacion']}»"
    return texto


def _proporcion(nombre: str, valor: Any, concepto: str) -> str:
    if not _numero(valor) or not 0 <= valor <= 1:
        raise ErrorDeCaso(f"{concepto}: la base no registra {nombre} numérica.")
    return f"{nombre} {valor}"


def mediciones(concepto: str, articulo: Articulo) -> list[dict[str, Any]]:
    items = articulo.evidencia.get(concepto)
    if not items:
        raise ErrorDeCaso(
            f"{concepto} no está en la evidencia de {articulo.condicion_id} en medsemiotics-db."
        )
    return items


def _valor(tipo: str, concepto: str, item: dict[str, Any]) -> str:
    if tipo == "estado":
        return ESTADOS.get(str(item.get("estado_lr")), str(item.get("estado_lr")))
    if tipo in ("lr+", "lr-"):
        if item.get("estado_lr") != "medido":
            raise ErrorDeCaso(f"{concepto}: no hay LR medido que citar ({item.get('estado_lr')}).")
        campo, etiqueta = ("lr_positivo", "LR+") if tipo == "lr+" else ("lr_negativo", "LR−")
        return _cociente(etiqueta, item.get(campo), concepto)
    campo = "sensibilidad" if tipo == "sens" else "especificidad"
    return _proporcion(campo, item.get(campo), concepto)


CAMPOS_TRAMO = {
    "lr+": ("lr_positivo", "ic95", "LR+"),
    "lr-": ("lr_negativo", "ic95_negativo", "LR−"),
}


def _valor_tramo(tipo: str, concepto: str, tramo: dict[str, Any], condiciones: bool) -> str:
    """Cifra de un tramo. En los tramos, los cocientes son números sueltos y su IC va aparte."""
    if tipo in CAMPOS_TRAMO:
        campo, campo_ic, etiqueta = CAMPOS_TRAMO[tipo]
        if not _numero(tramo.get(campo)):
            raise ErrorDeCaso(f"{concepto}: el tramo no registra {etiqueta}.")
        texto = _cociente(etiqueta, {"valor": tramo[campo], "ic95": tramo.get(campo_ic)}, concepto)
    else:
        campo = "sensibilidad" if tipo == "sens" else "especificidad"
        texto = _proporcion(campo, tramo.get(campo), concepto)
    return texto + _condiciones(tramo, tramo=True) if condiciones else texto


def tramos_de(item: dict[str, Any]) -> list[dict[str, Any]]:
    tramos = item.get("tramos")
    return [t for t in tramos if isinstance(t, dict)] if isinstance(tramos, list) else []


def _etiqueta_tramo(tramo: dict[str, Any]) -> str:
    for campo in ("umbral_condicion", "umbral", "poblacion"):
        if tramo.get(campo):
            return str(tramo[campo])
    return "tramo sin umbral declarado"


def resolver_token(
    tipo: str,
    concepto: str,
    articulo: Articulo,
    numero: int | None = None,
    tramo: int | None = None,
) -> str:
    """Resuelve un token. Si la base mide el hallazgo varias veces, ``@n`` elige una; sin índice
    se citan todas, cada una por su referencia si vienen de fuentes distintas y por su población
    si comparten fuente. ``#m`` cita el tramo m."""
    if tipo not in TIPOS:
        raise ErrorDeCaso(f"Token desconocido «{tipo}»; tipos válidos: {sorted(TIPOS)}")
    items = mediciones(concepto, articulo)
    if tramo is not None and tipo in ("hallazgo", "estado"):
        raise ErrorDeCaso(f"{concepto}#{tramo}: el token «{tipo}» no admite tramo.")
    if tipo == "hallazgo":
        return articulo.nombres[concepto]
    if numero is not None:
        if not 1 <= numero <= len(items):
            raise ErrorDeCaso(f"{concepto}@{numero}: la base registra {len(items)} medición(es).")
        items = [items[numero - 1]]
    if tramo is not None:
        if len(items) > 1:
            raise ErrorDeCaso(
                f"{concepto}#{tramo}: la base mide el hallazgo {len(items)} veces; "
                f"elija la medición con {concepto}@n#{tramo}."
            )
        tramos = tramos_de(items[0])
        if not 1 <= tramo <= len(tramos):
            raise ErrorDeCaso(f"{concepto}#{tramo}: la medición registra {len(tramos)} tramo(s).")
        if tipo in CAMPOS_TRAMO and items[0].get("estado_lr") != "medido":
            raise ErrorDeCaso(
                f"{concepto}: no hay LR medido que citar ({items[0].get('estado_lr')})."
            )
        return _valor_tramo(tipo, concepto, tramos[tramo - 1], condiciones=True)
    if len(items) == 1:
        return _valor(tipo, concepto, items[0])
    # Mediciones de fuentes distintas se identifican por su referencia; de la misma
    # fuente en poblaciones distintas, por la población.
    fuentes = [sorted(referencias_de(item)) for item in items]
    por_fuente = len({tuple(f) for f in fuentes}) == len(items)
    return "; ".join(
        f"{_valor(tipo, concepto, item)} "
        f"({', '.join(fuente) if por_fuente else item.get('poblacion') or f'medición {i}'})"
        for i, (item, fuente) in enumerate(zip(items, fuentes, strict=True), 1)
    )


def conceptos_citados(texto: str) -> set[str]:
    return {m["id"] for m in TOKEN.finditer(texto)}


def resolver(texto: str, articulo: Articulo, permitidos: Collection[str], donde: str) -> str:
    """Sustituye los tokens tras comprobar que el texto no trae cifras propias.

    ``permitidos`` son los hallazgos ya revelados en ese punto del caso: un token no puede
    adelantar evidencia que el estudiante todavía no tiene.
    """
    sin_tokens = TOKEN.sub(" ", texto)
    malformado = LLAVES.search(sin_tokens)
    if malformado:
        raise ErrorDeCaso(f"{donde}: token mal formado: {malformado[0]!r}")
    errores = [
        f"{donde}: {motivo} («{m[0]}»)"
        for patron, motivo in PROHIBIDOS
        for m in patron.finditer(sin_tokens)
    ]
    for concepto in sorted(conceptos_citados(texto) - set(permitidos)):
        errores.append(f"{donde}: {concepto} se cita antes de revelarse en una etapa.")
    if errores:
        raise ErrorDeCaso("\n".join(errores))

    def sustituir(m: re.Match[str]) -> str:
        valor = resolver_token(
            m["tipo"],
            m["id"],
            articulo,
            int(m["n"]) if m["n"] else None,
            int(m["t"]) if m["t"] else None,
        )
        if m["tipo"] == "hallazgo" and not _inicio_de_oracion(texto, m.start()):
            return _minuscula_inicial(valor)
        return valor

    return TOKEN.sub(sustituir, texto)


def _inicio_de_oracion(texto: str, posicion: int) -> bool:
    previo = texto[:posicion].rstrip(" «\"'")
    # Tras dos puntos, el español sigue en minúscula.
    return not previo or previo[-1] in ".?!¿¡\n"


def _minuscula_inicial(nombre: str) -> str:
    """«Fiebre» → «fiebre» dentro de una oración; las siglas («ECG», «VIH») no se tocan."""
    if len(nombre) > 1 and nombre[0].isupper() and nombre[1].islower():
        return nombre[0].lower() + nombre[1:]
    return nombre


def resumen(concepto: str, articulo: Articulo) -> list[dict[str, Any]]:
    """Fichas de un hallazgo tal como lo registra la base (una por población medida)."""
    items = mediciones(concepto, articulo)
    fichas: list[dict[str, Any]] = []
    for item in items:
        estado = str(item.get("estado_lr"))
        cifras: list[str] = []
        if estado == "medido":
            for tipo, campo in (("lr+", "lr_positivo"), ("lr-", "lr_negativo")):
                if item.get(campo):
                    cifras.append(_valor(tipo, concepto, item))
        for tipo, campo in (("sens", "sensibilidad"), ("esp", "especificidad")):
            if _numero(item.get(campo)):
                cifras.append(_valor(tipo, concepto, item))
        fichas.append(
            {
                "id": concepto,
                "nombre": articulo.nombres[concepto],
                "rol": ROLES.get(str(item.get("rol")), str(item.get("rol") or "")),
                "estado_lr": estado,
                "estado": ESTADOS.get(estado, estado),
                "poblacion": item.get("poblacion") if len(items) > 1 else None,
                "cifras": cifras,
                "decision": item.get("decision"),
                "motivo": item.get("motivo"),
                "advertencia": item.get("advertencia"),
                "graduacion": _graduacion(item.get("graduacion")),
                "tramos": [
                    {
                        "etiqueta": _etiqueta_tramo(tramo),
                        "cifras": [
                            _valor_tramo(tipo, concepto, tramo, condiciones=False)
                            for tipo, campo in TIPOS_TRAMO
                            if _numero(tramo.get(campo))
                        ],
                    }
                    for tramo in tramos_de(item)
                ],
                "referencias": sorted(referencias_de(item)),
            }
        )
    return fichas


TIPOS_TRAMO = (
    ("lr+", "lr_positivo"),
    ("lr-", "lr_negativo"),
    ("sens", "sensibilidad"),
    ("esp", "especificidad"),
)


def _graduacion(graduacion: Any) -> str | None:
    """«Diámetro aórtico máximo (cm), lectura acumulativa»: qué eje ordena los tramos."""
    if not isinstance(graduacion, dict) or not graduacion.get("parametro"):
        return None
    texto = str(graduacion["parametro"])
    if graduacion.get("unidad"):
        texto += f" ({graduacion['unidad']})"
    if graduacion.get("lectura") == "acumulativo":
        texto += ", lectura acumulativa: cada umbral cuenta los valores que lo superan"
    return texto


def referencias_de(item: Any) -> set[str]:
    encontrados: set[str] = set()

    def recorrer(valor: Any) -> None:
        if isinstance(valor, dict):
            for clave, contenido in valor.items():
                if clave == "ref" and isinstance(contenido, str):
                    encontrados.add(contenido)
                else:
                    recorrer(contenido)
        elif isinstance(valor, list):
            for contenido in valor:
                recorrer(contenido)

    recorrer(item)
    return encontrados
