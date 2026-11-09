# Depósito en Zenodo

**Pendiente del acuerdo escrito de los herederos.** Antes de ese acuerdo, la
integración GitHub–Zenodo permanece apagada. El acuerdo también precede a
cualquier trámite de los ISBN `10` y `11` en Bowker y a la declaración del
editor de la obra.

## Preparar la primera edición

1. Incorporar a los créditos y al formulario de Zenodo el editor que indique
   el acuerdo. Confirmar la revisión humana de las lecciones y la aprobación
   de los paratextos. Validar con `python -m lecciones check`, `python -m libro
   check`, `python -m pytest` y `cffconvert --validate`. Compilar la edición
   con `python -m libro build` y comprobar el PDF con `python -m libro check
   --exigir-pdf`.
2. Alinear la versión y la fecha real de publicación en `CITATION.cff` y
   `.zenodo.json`. Comparar ambos archivos con el mapa editorial. Deben figurar
   los cinco autores en su orden, Alcy Torres Catefort como autor fundador
   (legado), y el ORCID confirmado de Alcy Edmundo Torres Guerrero. Los demás
   identificadores quedan vacíos en el mapa y se omiten de los campos de
   catálogo hasta confirmación. Seleccionar **CC BY-NC-SA 4.0** para el libro.
   El código lleva su aviso MIT por separado.

## Depositar la edición autorizada

1. Desde [Zenodo](https://zenodo.org/), iniciar sesión con la cuenta autorizada
   y abrir un nuevo depósito de tipo **Publicación → Libro**. Cargar el PDF
   final, relacionarlo con el tag correspondiente del repositorio y completar
   título, descripción, idioma, autores, licencia y editor según los datos ya
   verificados. El depósito manual permite revisar el libro y los créditos
   antes de publicar. Si se elige la vía de GitHub del modelo original, activar
   el repositorio en [la integración](https://zenodo.org/account/settings/github/)
   antes de publicar la release y comprobar cómo se importan los metadatos.
   Elegir una sola vía para la misma edición.
2. Revisar la ficha final, el archivo, la licencia NoComercial, el editor y
   los cinco creadores antes de pulsar **Publish**. Si el acuerdo contempla la
   comunidad `powersemiotics`, enviar allí el registro para curaduría.
3. Tras la publicación, registrar en `CITATION.cff` el DOI de concepto y el DOI
   de la versión. Añadir al README la insignia del DOI de concepto. Para la
   siguiente edición, usar **New version** en el mismo registro y volver a
   verificar archivos y metadatos antes de publicar.

El DOI de concepto `10.5281/zenodo.22069641` identifica Medsemiotics. Conservar
en el nuevo registro la relación `isDerivedFrom` con el DOI de versión
`10.5281/zenodo.23862211`, que identifica el archivo de las primeras lecciones.
La corrección histórica de ese registro está documentada en
[Medsemiotics](https://github.com/alcyedmundo281/medsemiotics/tree/main/docs/correcciones/zenodo-v1.1.0).

[Guía de depósitos de Zenodo](https://help.zenodo.org/docs/deposit/)
· [Licencias](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
· [Metadatos de GitHub](https://help.zenodo.org/docs/github/describe-software/zenodo-json/)
