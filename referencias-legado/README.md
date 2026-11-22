# Referencias del legado

Transcripción **no canónica** de *Neurología Pediátrica* (la fuente declara «3ra. EDICION»), una
ficha YAML por capítulo. Es material de trabajo para escribir las lecciones, **no es texto del
libro**: cada lección se escribe desde cero (ADR-001, D3).

- **No es canónica.** La hizo una persona y tiene errores de transcripción, no tiene números de
  página y le faltan las figuras y las tablas. Lo que vale es el impreso.
- **No se cita desde aquí.** Un pasaje solo entra en un bloque `::: {.legado}` después de
  contrastarlo con la fotografía de su página, y el cotejo se registra en
  `lecciones/legado-cotejo.yaml`.
- **Solo la obra de la familia.** No se incluyen los preliminares (prólogos, coautores,
  dedicatorias) ni los capítulos de autores ajenos a la familia. Las fichas no llevan firmas.
  Un capítulo que en la fuente no es del autor fundador lleva
  `autoria_distinta_del_autor_fundador: true` y `citable_como_legado: false`.
- **Derechos.** Este texto no forma parte de la licencia CC BY-NC-SA 4.0 de las lecciones ni del
  libro. Sus derechos corresponden a sus titulares.

Las fichas se generan con `tools/fuentes/transcripcion.py` desde el archivo original, que no está
en el repositorio; su SHA-256 figura en cada ficha. No se editan a mano.
