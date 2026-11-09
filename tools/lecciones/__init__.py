"""Lecciones: la fuente única del texto de Medsemiotics (blog y libro).

Cada lección vive en ``lecciones/<id>.qmd``: frontmatter YAML con el contrato editorial y
un cuerpo Quarto con secciones fijas. El blog y el libro son proyecciones de ese archivo.

Reglas que este paquete hace cumplir (ADR-001, ``docs/adr/ADR-001-arquitectura-libro.md``):

- Las cifras de rendimiento diagnóstico (LR, sensibilidad, especificidad, IC) solo entran
  por token ``{{tipo HM:####}}`` desde medsemiotics-db; nunca se escriben a mano.
- Cualquier otra cifra del cuerpo va en un párrafo con cita ``[@clave]`` de ``lecciones/refs.bib``,
  y cada entrada de esa bibliografía lleva PMID y DOI, verificables con ``lecciones citas``.
- ``estado`` sigue borrador → revisado → publicado; pasar de borrador exige un revisor humano
  nominado. La salida de un LLM es un borrador.
- Las imágenes vienen de Wikimedia Commons o son ilustraciones originales hechas por personas:
  nunca fotografías de pacientes ni imágenes generadas con IA.

El validador estructural y el verificador de citas se adaptaron de ``biosemiotics``
(``scripts/validacion.py`` y ``scripts/verificar_citas.py``) sin modificar ese repositorio.
"""
