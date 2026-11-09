# Lecciones

Cada `<id>.qmd` es la fuente del capítulo del libro y su proyección autónoma. La arquitectura y sus razones están en
[`docs/adr/ADR-001-arquitectura-libro.md`](../docs/adr/ADR-001-arquitectura-libro.md).

- Una lección por archivo; el nombre del archivo es su `id`.
- Se parte de [`assets/plantilla-leccion.qmd`](../assets/plantilla-leccion.qmd).
- Las cifras de rendimiento diagnóstico entran solo por token desde
  [medsemiotics-db](https://github.com/alcyedmundo281/medsemiotics-db); cualquier otra cifra
  lleva su cita `[@clave]` de `refs.bib`.
- `estado: borrador` hasta que un revisor humano nominado la apruebe.
- Cada lección declara en `uso_ia` dónde intervino la inteligencia artificial; la declaración
  completa de la obra está en [`AI-USE.md`](AI-USE.md).
- Los módulos HTML de clase (`neurologia/*.html`) no se tocan: se enlazan en `modulos_html`.

```bash
python -m lecciones check   # contrato editorial (sin red)
python -m lecciones citas   # refs.bib contra PubMed y Crossref (requiere red)
```
