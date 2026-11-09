# Neurología clínica para el médico general

**Semiología basada en la evidencia, del recién nacido al adulto.**

La obra continúa el legado de Alcy Torres Catefort y reúne las contribuciones
de Alcy Ramiro Torres Guerrero, Gladys Torres Guerrero, Alcy Edmundo Torres
Guerrero y Daniela Torres Tobar.

## El libro

El [mapa maestro](mapa-maestro-libro.md) registra el plan y el estado de cada
lección. [Las fuentes Quarto y los paratextos](lecciones/) se trasladaron desde
[Medsemiotics](https://github.com/alcyedmundo281/medsemiotics/tree/0c14e511cf210e395967ff9640da3e992bd9f70f/lecciones).
El [manifiesto de procedencia](docs/procedencia.md) identifica el árbol original.
Los [módulos interactivos](https://powersemiotics.com/medsemiotics/neurologia.html)
siguen en la plataforma docente.

## Uso

Con Python 3.12, instale las dependencias y añada `tools/` a `PYTHONPATH`.

```bash
python -m pip install -r requirements.txt
export PYTHONPATH=tools                 # PowerShell: $env:PYTHONPATH = 'tools'
python -m lecciones check
python -m libro check
python -m pytest
cffconvert --validate
python -m libro qmd --incluir-borradores --semblanzas-pendientes
```

El último comando genera una vista previa en `build/quarto/`. Para la edición
revisada, `python -m libro build` usa Quarto, LuaLaTeX y `pdfinfo`, y exige
la aprobación de los paratextos. La opción `--material-previo` consulta una
copia de Medsemiotics indicada en `NEUROLOGY_MEDSEMIOTICS`. Ese apéndice se
compone por separado para la vista previa.

## Fuentes

Las cifras clínicas provienen de [medsemiotics-db](https://github.com/alcyedmundo281/medsemiotics-db).
Las dos fichas necesarias para resolver los tokens de la lección conservan
la misma revisión de la base. La ficha de meningitis en `posts/` y los
resúmenes previos de módulos en `assets/libro/modulos.yaml` proceden de
Medsemiotics y conservan [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Al actualizar la evidencia, genere las fichas juntas desde un solo commit de
medsemiotics-db con `Source` y `make_post` de `tools/generate_topic.py`
en Medsemiotics. El contrato comprueba que los tokens resuelvan y que las
revisiones coincidan.

## Cómo citar

Use [CITATION.cff](CITATION.cff) para citar el repositorio. Los datos de la futura
edición están en [.zenodo.json](.zenodo.json) y el procedimiento sujeto al
acuerdo de los herederos en [deposito-zenodo.md](deposito-zenodo.md).

## Licencia

Las lecciones, los paratextos y el libro se distribuyen bajo
[CC BY-NC-SA 4.0](LICENSE). El código se distribuye bajo [MIT](LICENSE-CODIGO).
