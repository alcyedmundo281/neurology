# Declaración de uso de inteligencia artificial

**Obra:** *Neurología clínica para el médico general*, sobre la obra de
Alcy Torres Catefort (*Neuropediatría–Urgencias*, 1991; *Neurología Pediátrica*, 1993)
**Autores responsables:** Alcy Ramiro Torres Guerrero ·
Gladys Torres Guerrero · Alcy Edmundo Torres Guerrero
([ORCID 0000-0002-9742-375X](https://orcid.org/0000-0002-9742-375X)), coordinación editorial ·
Daniela Torres Tobar, autoevaluaciones de toda la obra
**Autor fundador:** Alcy Torres Catefort (†), cuya obra se cita, no se reescribe en su nombre
**Editor de la obra:** pendiente del acuerdo escrito de los herederos.
**Alcance:** las lecciones de `lecciones/`, sus proyecciones y las ediciones del libro (PDF, EPUB, Kindle e impresa).
**Colofón:** el párrafo breve que lleva cada edición vive en
`lecciones/paratextos/declaracion-ia.md`; si cambia uno, revise el otro.
**Vigente desde:** 30 de octubre de 2026

---

## Por qué existe este archivo

No se puede verificar si alguien «usó inteligencia artificial». El uso no se puede
detectar, y los detectores disponibles clasifican falsamente como generado por máquina más
de la mitad de los textos escritos por autores cuya lengua materna no es el inglés.¹

Lo que sí se puede verificar es **de dónde viene cada afirmación**. Este archivo declara el
uso de IA y el repositorio permite comprobar esa procedencia. Esta obra tiene además una
deuda particular: continúa el libro de un maestro que ya no puede revisar lo que se diga en
su nombre. Por eso la frontera entre su voz, la de sus hijos y la de una máquina tiene que
quedar trazada.

---

## Qué herramientas y en qué etapas

| Herramienta | Etapa | Qué hace |
|---|---|---|
| Adobe Scan y Tesseract (OCR) | Transcripción de la edición de 1993 | Reconocimiento óptico de caracteres sobre los escaneos. |
| Claude (Claude Code) | Transcripción, búsqueda bibliográfica, borradores, código | Corrige el OCR contra la imagen de la página, busca en PubMed, propone borradores de lecciones y escribe las herramientas de validación. Propone; no decide. Trabaja bajo `CLAUDE.md` y `AGENTS.md`. |
| Codex (revisión de PR en GitHub) | Revisión del código | Señala defectos en los cambios propuestos; cada hallazgo se verifica antes de corregirlo. |

Cada lección declara en su campo `uso_ia` en qué etapas intervino la IA:
`transcripcion`, `busqueda-bibliografica`, `redaccion-borrador`, `revision-estilo` o
`codigo`. Una lista vacía declara que no intervino. `lecciones check` rechaza una lección
sin esa declaración.

**El compilador no usa inteligencia artificial.** Las herramientas de `tools/lecciones` y
`tools/libro` son Python determinista. La verificación de citas es una consulta a PubMed y
Crossref, no la inferencia de un modelo.

---

## Qué no hace la inteligencia artificial en esta obra

Estas prohibiciones no son promesas. Están escritas en el contrato de la lección
(`docs/adr/ADR-001-arquitectura-libro.md`), y el validador hace cumplir varias de ellas.

- **No genera imágenes.** Las figuras vienen de Wikimedia Commons o son ilustraciones
  originales hechas por personas, con autor declarado. Las fotografías de recién nacidos
  de las ediciones de 1991 y 1993 no se reproducen.
- **No produce referencias.** Ninguna cita se acepta de un modelo sin verificar su PMID
  contra PubMed y su DOI contra Crossref (`uv run python -m lecciones citas`).
- **No aporta cifras clínicas.** Los cocientes de verosimilitud, la sensibilidad, la
  especificidad y los intervalos de confianza entran solo por token desde medsemiotics-db.
  Cualquier otra cifra va con su cita. El validador rechaza las métricas escritas a mano.
- **No habla por el autor fundador.** Lo que se atribuye a Alcy Torres Catefort es cita
  literal de su obra, con su página, dentro de los bloques «Legado». El resto del texto es
  nuevo y responde a los autores vivos.
- **No inventa pacientes.** Las viñetas clínicas son sintéticas y docentes.
- **No autoriza publicaciones.** Toda lección escrita con asistencia de IA es un borrador
  hasta que su revisor nominado la aprueba. El agente nunca es revisor, y el validador lo
  impide.

---

## Qué decisiones no se delegan

La inteligencia artificial **no es autora** de esta obra y no puede serlo, porque no puede
asumir responsabilidad por lo que afirma.² No pierde una licencia profesional ni responde
si una recomendación causa daño.

Quedan a cargo de los autores humanos:

- El **juicio clínico** de cada lección: qué se enseña, con qué límites y qué decisión se
  recomienda.
- La sección de **límites** («dónde no confiar») de cada lección, que es obligatoria.
- La **revisión de cada lección**, que hace el editor, Alcy Edmundo Torres Guerrero, como
  revisor humano nominado de toda la obra. El especialista de cada área (neuropediatría,
  Alcy Ramiro Torres Guerrero; neuroftalmología, Gladys Torres Guerrero) es su autor.
- El **cotejo de la transcripción de 1993** contra el impreso.
- La **verificación final de cada cita** y la responsabilidad por el plagio.
- La **decisión de publicar**, en cualquier edición y canal de venta.

---

## Confidencialidad

No se cargan a servicios de inteligencia artificial datos de pacientes ni manuscritos
confidenciales de terceros. Los escaneos de la obra de 1993 son de la familia del autor y
se procesan con su autorización. Se guardan fuera del repositorio público (`fuentes/`).

---

## Cómo comprobarlo usted mismo

Esta declaración no pide que se le crea. El repositorio es público:

```bash
git clone https://github.com/alcyedmundo281/medsemiotics
cd medsemiotics
uv sync && npm ci

uv run python -m lecciones check   # contrato de cada lección, incluida su declaración uso_ia
uv run python -m lecciones citas   # cada PMID contra PubMed y Crossref
```

Si encuentra un error, ábralo como *issue*. Es exactamente lo que esta declaración pide.

---

## Qué ya falló

Una declaración que solo enumera buenas prácticas no es verificable. Estos fallos ya
ocurrieron en el trabajo de esta edición:

- **Una página incompleta, rellenada con una conjetura.** Al transcribir el capítulo I, a
  la foto de la página 16 le faltaba el comienzo de un ítem. El modelo puso como título el
  pie de la figura vecina («Reflejo tónico de los flexores de los dedos»). Al volver a
  fotografiar la página apareció el título real: «*Grasping* de pies». La conjetura estaba
  marcada como faltante, y por eso se pudo corregir.
- **Una recomendación hecha antes de verificar.** El modelo recomendó firmar con un
  apellido compuesto con guion sin comprobar cómo estaba ya indexado uno de los autores en
  PubMed. Al comprobarlo se retiró la recomendación, porque habría dividido sus citas.
- **Una fuente secundaria con datos contradictorios.** Una enciclopedia generada por IA
  sobre el autor fundador daba fechas que no coincidían con las de su propia fuente. Los
  datos biográficos se confirman con la familia y con fuentes primarias.
- **Tres defectos en el propio validador**, señalados por la revisión automática del PR
  #34: reglas de evidencia que no se aplicaban al frontmatter clínico, citas agrupadas que
  validaban solo la última clave, y años de las claves de cita leídos como cifras. Se
  corrigieron con pruebas antes de fusionar.

- **Un autor inventado en la portada del libro.** En el PR #33 (generador del libro impreso)
  un agente escribió un autor que no existe, «Alcy Montserrat», con un ORCID
  (0009-0001-7627-9895) que no pertenece a la obra. El nombre quedó en tres sitios:
  la portada (`assets/libro/preambulo.tex`), los valores de respaldo de `tools/libro/datos.py`
  y una prueba de `pdfinfo` que repetía el nombre en vez de comprobarlo. Pasó los gates
  porque ninguna prueba comparaba la autoría de la portada con una fuente: las pruebas
  fijaban incluso el DOI de la plataforma como DOI del libro. Lo señaló el autor
  coordinador al revisar los autores del libro. Ahora la autoría y la licencia salen solo de `lecciones/mapa.yaml`
  (`obra` y `personas`), sin valores de respaldo (si falta un dato, el libro no se genera), la
  portada y los créditos se generan desde esos datos, una prueba exige los cuatro autores
  reales en su orden en la portada y en los créditos, y otra falla si en `assets/`, `tools/` o
  `lecciones/` aparece un nombre de persona de la familia de la obra o un ORCID que no esté
  en `personas`.

El modo de falla de estas herramientas no es razonar mal: es afirmar con seguridad algo
cuya procedencia no pueden sostener. Los controles existen porque el fallo ocurre.

---

## Notas

1. Liang W, Yuksekgonul M, Mao Y, Wu E, Zou J. GPT detectors are biased against non-native
   English writers. *Patterns*. 2023;4(7):100779. doi:10.1016/j.patter.2023.100779
2. ICMJE. *Recommendations for the Conduct, Reporting, Editing, and Publication of
   Scholarly Work in Medical Journals*, sección sobre inteligencia artificial.

---

*Este archivo se versiona con la obra. Su historial de cambios está en el repositorio.*
