---
id: HM6049-01
slug: paralisis-cerebral-precision-semiotica
title: 'Parálisis cerebral: hallazgos y evidencia clínica'
subtitle: Hallazgos y criterios clínicos sin cocientes de verosimilitud medidos.
date: '2026-11-01'
author: Alcy E. Torres-Guerrero
category: medicina_interna
category_label: Medicina Interna
tags:
- medicina_interna
- paralisis-cerebral
- semiologia
reading_time: 8 min
difficulty: Intermedio
fuente:
  repositorio: alcyedmundo281/medsemiotics-db
  revision: ea2f6e63b8508e6a36a28fd11950bd28c0900a49
  doi: 10.5281/zenodo.22064424
  condicion: condiciones/HM6049-paralisis-cerebral.yaml
  archivos:
    CITATION.cff: 6e9c73a515bb6225965edda4efc52104a4e3b9776dab1bd4fce8e643d86eb1d2
    conceptos/HM0500-sintoma-neurologico.yaml: bfed2fddf9ee375171804badb4977b28916322ec3dc288af10da4918cd035044
    conceptos/HM3246-ausencia-de-movimientos-fidgety.yaml: fdf315ac6e39d7397ff63604c905474fb029cb58a193d3db30c8af459020a8c2
    condiciones/HM6049-paralisis-cerebral.yaml: e140c5a00632e0529acb40501e524f61bbc8e32edbea9f0d945af899dc073c13
    referencias/pmid-15856440.yaml: 7e8ba5754fd20bab852ab0f45ec0019784b23a0dcf44858a808bee88373fbfab
    referencias/pmid-28715518.yaml: e8bd0dee3a08f98ab574364e9f449399e67ec3c252f89fd1947ddff78f9c54b4
grounding:
  condicion_id: HM:6049
  condicion_nombre: Parálisis cerebral
  concepto_id: HM:3246
  concepto_nombre: Ausencia de movimientos generales de tipo fidgety (3-5 meses)
  estado_lr: no_medido
  lr_positivo: null
  lr_negativo: null
  lr_positivo_rango: null
  lr_negativo_rango: null
  poblacion: null
  referencia_id: pmid:15856440
  referencia_cita: 'Einspieler C, Prechtl HF Prechtl''s assessment of general movements: a diagnostic tool for the functional assessment of the young nervous system Ment Retard Dev Disabil Res Rev 2005'
  pmid: '15856440'
  doi: 10.1002/mrdd.20051
  sensibilidad: 0.95
  especificidad: 0.95
triada:
  significante: Ausencia de movimientos generales de tipo fidgety (3-5 meses)
  significado: El mecanismo fisiopatológico no está documentado en esta fuente.
  decision: La fuente no documenta una decisión específica para este hallazgo.
evidencia:
- concepto: HM:3246
  rol: apoyo
  estado_lr: no_medido
  sensibilidad: 0.95
  especificidad: 0.95
  ref_rendimiento: pmid:15856440
  motivo: el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí
  nota: la valoración conjunta (movimientos generales anormales persistentes de tipo cramped-synchronized o ausencia de fidgety) predice la parálisis cerebral posterior según los autores del método; revisión narrativa, no sistemática
autoevaluacion:
- id: q1
  pregunta: En Parálisis cerebral, ¿qué estado de la evidencia corresponde a «Ausencia de movimientos generales de tipo fidgety (3-5 meses)» según la fuente?
  concepto_id: HM:3246
  referencia_id: null
  pmid: null
  doi: null
  fuente_doi: 10.5281/zenodo.22064424
  evidencia:
    condicion_id: HM:6049
    concepto_id: HM:3246
    estado_lr: no_medido
    campo: null
    dato: null
    poblacion: null
    motivo: el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí
    decision: null
    advertencia: null
  opciones:
  - texto: Sin efecto discriminativo
    correcta: false
    feedback: 'La fuente clasifica este hallazgo como «LR no medido». LR no medido Motivo: el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí.'
  - texto: LR no medido
    correcta: true
    feedback: 'LR no medido Motivo: el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí.'
  - texto: LR no medible
    correcta: false
    feedback: 'La fuente clasifica este hallazgo como «LR no medido». LR no medido Motivo: el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí.'
---

# Parálisis cerebral

Hallazgos y criterios clínicos sin cocientes de verosimilitud medidos.

## Nombre en inglés

Cerebral palsy

## Códigos

Snomed: 128188000; Cie10: No documentado.

## Hallazgos clínicos

### Ausencia de movimientos generales de tipo fidgety (3-5 meses) (HM:3246)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR no medido

**Sensibilidad:** 0.95

**Especificidad:** 0.95

**Ref rendimiento:** pmid:15856440

**Motivo:** el resumen declara «sensibilidad y especificidad del 95% cada una» para la valoración de los movimientos generales, pero no publica el cociente, la población ni el diseño; no se calcula aquí

**Nota:** la valoración conjunta (movimientos generales anormales persistentes de tipo cramped-synchronized o ausencia de fidgety) predice la parálisis cerebral posterior según los autores del método; revisión narrativa, no sistemática

## Aspectos pendientes de documentación

Decisión clínica: el rol de la arista (apoyo) es provisional. La sensibilidad declarada permitiría prueba_sensible, pero la fuente es una revisión narrativa de los autores del método y no da población.

Novak 2017 (pmid:28715518, revisión sistemática y guía de diagnóstico precoz) está en referencias/ pero SIN citar: tiene una errata («Error in Table», JAMA Pediatr 2017;171(9):919, doi:10.1001/jamapediatrics.2017.3169) cuyo texto no se pudo leer el 2026-10-31 (jamanetwork.com devolvió 403 y Europe PMC no la indexa con texto). Hasta cotejarla, no se transcriben de ella las sensibilidades de la resonancia, de los movimientos generales ni del HINE.

Sin CIE-10 verificado (navegador de la OMS fuera de servicio el 2026-10-31).

## Referencias y procedencia

**pmid:15856440:** Prechtl's assessment of general movements: a diagnostic tool for the functional assessment of the young nervous system. Ment Retard Dev Disabil Res Rev, 2005. DOI: 10.1002/mrdd.20051.

**pmid:28715518:** Early, Accurate Diagnosis and Early Intervention in Cerebral Palsy: Advances in Diagnosis and Treatment. JAMA Pediatr, 2017. DOI: 10.1001/jamapediatrics.2017.1689.

Fuente clínica: medsemiotics-db, condición HM:6049.
