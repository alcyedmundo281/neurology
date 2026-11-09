"""Vista Markdown de un caso compilado, para revisión humana antes de aprobarlo."""

from __future__ import annotations

from typing import Any


def _tabla(datos: list[dict[str, str]]) -> list[str]:
    if not datos:
        return []
    filas = ["| Dato | Hallazgo |", "| :--- | :--- |"]
    filas += [f"| {d['etiqueta']} | {d['valor']} |" for d in datos]
    return ["\n".join(filas)]


def autores_texto(autoria: dict[str, Any]) -> str:
    """Los autores con su firma bibliográfica (la persona real, no un nombre genérico)."""
    return ", ".join(a.get("nombre_bibliografico") or a["nombre"] for a in autoria["autores"])


def markdown(caso: dict[str, Any]) -> str:
    pub = caso["publicacion"]
    lineas = [
        f"# Caso socrático · {caso['condicion_id']} · {caso['slug']}",
        f"Estado: **{caso['estado']}** · Versión {pub['version']} · "
        f"Publicado: {pub['fecha'] or '—'} · Autoría: {autores_texto(caso['autoria'])} · "
        f"Revisor: {caso['autoria']['revisor'] or 'pendiente'}",
        f"> {caso['aviso']}",
        "## Objetivos",
        *(f"- {o}" for o in caso["objetivos"]),
        f"## Viñeta: {caso['vineta']['titulo']}",
        caso["vineta"]["texto"],
        *_tabla(caso["vineta"]["datos"]),
    ]
    for etapa in caso["etapas"]:
        lineas.append(f"## Etapa {etapa['numero']} · {etapa['fase_etiqueta']}: {etapa['titulo']}")
        if etapa["informacion"]:
            lineas.append(etapa["informacion"])
        lineas.extend(_tabla(etapa["datos"]))
        for h in etapa["hallazgos"]:
            cifras = "; ".join(h["cifras"]) or h["estado"]
            lineas.append(
                f"- **[medsemiotics-db] {h['nombre']}** ({h['rol']}): {cifras}"
                + (f". {h['decision']}" if h["decision"] else "")
                + (f". **Advertencia:** {h['advertencia']}" if h["advertencia"] else "")
            )
            if h["tramos"]:
                # Numerados como en el token: {{lr+ HM:3012#2}} cita el tramo 2.
                tramos = [f"  Tramos · {h['graduacion'] or 'sin graduación declarada'}:"]
                tramos += [
                    f"  {i}. {t['etiqueta']}: {'; '.join(t['cifras'])}"
                    for i, t in enumerate(h["tramos"], 1)
                ]
                lineas.append("\n".join(tramos))
        for p in etapa["preguntas"]:
            lineas += [f"**Pregunta:** {p['pregunta']}", f"*Clave docente:* {p['clave']}"]
    lineas += [
        "## Cierre",
        caso["cierre"]["sintesis"],
        "**Necesidades de aprendizaje:**",
        *(f"- {n}" for n in caso["cierre"]["necesidades_aprendizaje"]),
    ]
    if caso["omitidos"]:
        lineas.append("## Hallazgos de la base no usados en el caso")
        lineas += [f"- {o['nombre']} ({o['id']}): {o['motivo']}" for o in caso["omitidos"]]
    lineas.append("## Referencias")
    lineas += [f"- {r['id']}: {r['cita']}" for r in caso["referencias"]]
    return "\n\n".join(lineas)
