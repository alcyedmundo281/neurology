---
id: HM6004-01
slug: meningitis-aguda-sacudida-cefalica
title: 'Meningitis aguda: hallazgos y evidencia clínica'
subtitle: Hallazgos, cocientes documentados y límites de la evidencia.
date: '2026-08-20'
author: Alcy E. Torres-Guerrero
category: neurologia
category_label: Neurología
tags:
- criterios
- meningitis-aguda
- neurologia
- semiologia
reading_time: 8 min
difficulty: Intermedio
fuente:
  repositorio: alcyedmundo281/medsemiotics-db
  revision: ea2f6e63b8508e6a36a28fd11950bd28c0900a49
  doi: 10.5281/zenodo.22064424
  condicion: condiciones/HM6004-meningitis-aguda.yaml
  archivos:
    CITATION.cff: 6e9c73a515bb6225965edda4efc52104a4e3b9776dab1bd4fce8e643d86eb1d2
    conceptos/HM0100-signo-vital-alterado.yaml: 3e0914bff0c0dc8f1a07185d49c70c4ee7dcf11cfa7ebc3281d611f5abb4f504
    conceptos/HM0101-fiebre.yaml: d8367b5824cbb321094893d8dde57e082205ace1ba21a89144af01209279e45e
    conceptos/HM0200-dolor.yaml: 583f1c01f2eeeed369469010e4b7d24d73d883bc3ef40266f80eaa0db0089463
    conceptos/HM0207-cefalea.yaml: 3a7957f3f8cda87461090f0aff7e5cccde0cbea0a59b1bd8716a6fb509bb4b8c
    conceptos/HM0300-sintoma-digestivo.yaml: 2c9dfe41462c5927070d1020039bd0dac823bcf998d53ac0a7d8e04ccab240aa
    conceptos/HM0301-nauseas.yaml: e678ffbd65c8ecbae1afe311de0693dc240bff7d676879838347df44fa30556a
    conceptos/HM0302-vomitos.yaml: c2a3e83028a5dbb8b5d22771c6f413648cbe087e1f3dffa381f416e6bc5a12c9
    conceptos/HM0500-sintoma-neurologico.yaml: bfed2fddf9ee375171804badb4977b28916322ec3dc288af10da4918cd035044
    conceptos/HM0501-alteracion-del-nivel-de-conciencia.yaml: c3d0515c056d2458152b77498e02ec985a7f67d31c63bec961722da48ac6d980
    conceptos/HM3005-rigidez-de-nuca.yaml: acf2a79e35697ca46f2a084ef549f5345ad4d40e9014474088cb2f897f43e9c7
    conceptos/HM3006-acentuacion-cefalea-sacudida.yaml: b7e237eb2e3f5ead09a07aff8832f8b79afc05a258a7649cc778aba725441a12
    conceptos/HM3238-signo-de-kernig.yaml: 97a5f88234b70ede1cfe5c8adb4c99c64c38397f63af19a502c9fcc41acfa529
    conceptos/HM3239-signo-de-brudzinski.yaml: 8550100892b0b06d7f506a534f89c5266e9fbd7d65a416ebb7e99807a25195b8
    conceptos/HM3240-fontanela-abombada.yaml: 73b922db809138632d714f8d73b419f42b7b04174a6cdc285b7f83e8508a75b8
    condiciones/HM6004-meningitis-aguda.yaml: 28214ecff71d433fa1e1711beeb79efba5a7cf303059b9dc4b5bb6d5cf2f90f3
    referencias/pmid-10411200.yaml: 8b029e69cf573d005a0416d103199e091dfd7156895fad9de3768aebf43a5eab
    referencias/pmid-12060874.yaml: d3b3a5af84554f3adb5d3e92fa97d6422410beaa5173f8b29388b47cec1e99bf
    referencias/pmid-20974781.yaml: 45ab43b70e8f77a5c15c43d807610f7300cd78a6780de423402428cd4badc338
    referencias/pmid-32524581.yaml: 5678973f38f01ba507942f774c9e5017c7f05fb3673b8de2be79063ca172571b
grounding:
  condicion_id: HM:6004
  condicion_nombre: Meningitis aguda
  concepto_id: HM:3005
  concepto_nombre: Rigidez de nuca
  estado_lr: medido
  lr_positivo: 0.94
  lr_negativo: null
  lr_positivo_rango: null
  lr_negativo_rango: null
  poblacion: null
  referencia_id: pmid:12060874
  referencia_cita: Thomas KE, Hasbun R, Jekel J, Quagliarello VJ The diagnostic accuracy of Kernig's sign, Brudzinski's sign, and nuchal rigidity in adults with suspected meningitis Clin Infect Dis 2002
  pmid: '12060874'
  doi: 10.1086/340979
  sensibilidad: 0.3
triada:
  significante: Rigidez de nuca
  significado: El mecanismo fisiopatológico no está documentado en esta fuente.
  decision: La fuente no documenta una decisión específica para este hallazgo.
evidencia:
- concepto: HM:3006
  rol: apoyo
  estado_lr: no_medido
  sensibilidad: 0.653
  ic95_sensibilidad:
  - 0.373
  - 0.856
  especificidad: 0.704
  ic95_especificidad:
  - 0.477
  - 0.861
  poblacion: pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR
  ref: pmid:32524581
  motivo: la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí
  nota: sin alteración de la conciencia (8 estudios, 921 participantes), Se 0.752 (IC95% 0.543-0.886) y Sp 0.608 (IC95% 0.434-0.759). Sustituye al LR+ 2.2 y LR− 0 de Attia 1999 (pmid:10411200), que venían de un único estudio de 1991
  decision: una prueba negativa no excluye la meningitis; no evita la punción lumbar
- concepto: HM:0207
  rol: manifestacion
  estado_lr: no_medido
  sensibilidad: 0.5
  ic95_sensibilidad:
  - 0.32
  - 0.68
  ref_rendimiento: pmid:10411200
  motivo: la fuente publica sensibilidad agrupada pero no especificidad, así que el cociente no es calculable desde el abstract
- concepto: HM:0301
  rol: manifestacion
  estado_lr: no_medido
  sensibilidad: 0.3
  ic95_sensibilidad:
  - 0.22
  - 0.38
  ref_rendimiento: pmid:10411200
  motivo: sensibilidad agrupada sin especificidad; LR no calculable
- concepto: HM:0302
  rol: manifestacion
  estado_lr: no_medido
  sensibilidad: 0.3
  ic95_sensibilidad:
  - 0.22
  - 0.38
  ref_rendimiento: pmid:10411200
  motivo: la fuente agrupa náuseas y vómitos en una sola estimación
- concepto: HM:0101
  rol: prueba_sensible
  estado_lr: no_medido
  motivo: forma parte de la tríada fiebre + rigidez de nuca + alteración del estado mental, cuya presencia de al menos uno tiene sensibilidad del 99-100%. La fuente no desglosa el cociente de cada componente por separado.
- concepto: HM:3005
  rol: apoyo
  estado_lr: medido
  sensibilidad: 0.3
  lr_positivo: &id001
    valor: 0.94
    ref: pmid:12060874
    poblacion: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR
  ref: pmid:12060874
  nota: Attia 1999 (pmid:10411200) no publica su cociente aislado; este es de Thomas 2002. La fuente solo le halla valor en los 4 pacientes con ≥ 1000 leucocitos en el LCR
- concepto: HM:3238
  rol: apoyo
  estado_lr: medido
  sensibilidad: 0.05
  lr_positivo:
    valor: 0.97
    ref: pmid:12060874
    poblacion: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR
  ref: pmid:12060874
- concepto: HM:3239
  rol: apoyo
  estado_lr: medido
  sensibilidad: 0.05
  lr_positivo:
    valor: 0.97
    ref: pmid:12060874
    poblacion: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR
  ref: pmid:12060874
- concepto: HM:3240
  rol: apoyo
  estado_lr: medido
  lr_positivo:
    valor: 3.5
    ic95:
    - 2.0
    - 6.0
    ref: pmid:20974781
    poblacion: niños (revisión sistemática de 10 estudios prospectivos) con meningitis bacteriana confirmada en laboratorio frente a niños sin ella; hallazgo en la exploración
  ref: pmid:20974781
  nota: Curtis 2010 publica además un LR 8.00 (IC95% 2.4-26) cuando el abombamiento se obtiene por la historia (referido por quien cuida al niño), distinto del hallazgo explorado. La fuente no publica LR− para este signo, y concluye que ningún signo aislado es diagnóstico
  decision: aumenta la probabilidad de meningitis bacteriana en el niño; no la confirma y su ausencia no la descarta
- concepto: HM:0501
  rol: prueba_sensible
  estado_lr: no_medido
  motivo: componente de la tríada; la fuente no publica su cociente aislado
autoevaluacion:
- id: q1
  pregunta: En Meningitis aguda, ¿cuál es el resultado documentado del LR positivo para «Rigidez de nuca»?
  concepto_id: HM:3005
  referencia_id: pmid:12060874
  pmid: '12060874'
  doi: 10.1086/340979
  fuente_doi: 10.5281/zenodo.22064424
  evidencia:
    condicion_id: HM:6004
    concepto_id: HM:3005
    estado_lr: medido
    campo: lr_positivo
    dato: *id001
    poblacion: null
    motivo: null
    decision: null
    advertencia: null
  opciones:
  - texto: La fuente no dispone de un cociente medido para este hallazgo.
    correcta: false
    feedback: 'Sí hay una medición documentada: LR positivo: 0.94. LR positivo: 0.94.'
  - texto: 'LR positivo: 0.94.'
    correcta: true
    feedback: 'LR positivo: 0.94.'
  - texto: El valor 0.94 corresponde al LR negativo y no al LR positivo.
    correcta: false
    feedback: 'Ese número corresponde al LR positivo, no al LR negativo. LR positivo: 0.94.'
- id: q2
  pregunta: En Meningitis aguda, ¿qué estado de la evidencia corresponde a «Acentuación de la cefalea con la sacudida cefálica» según la fuente?
  concepto_id: HM:3006
  referencia_id: pmid:32524581
  pmid: '32524581'
  doi: 10.1002/14651858.CD012824.pub2
  fuente_doi: 10.5281/zenodo.22064424
  evidencia:
    condicion_id: HM:6004
    concepto_id: HM:3006
    estado_lr: no_medido
    campo: null
    dato: null
    poblacion: pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR
    motivo: la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí
    decision: una prueba negativa no excluye la meningitis; no evita la punción lumbar
    advertencia: null
  opciones:
  - texto: LR no medido
    correcta: true
    feedback: 'LR no medido Población: pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR. Motivo: la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí. Interpretación registrada: una prueba negativa no excluye la meningitis; no evita la punción lumbar.'
  - texto: LR no medible
    correcta: false
    feedback: 'La fuente clasifica este hallazgo como «LR no medido». LR no medido Población: pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR. Motivo: la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí. Interpretación registrada: una prueba negativa no excluye la meningitis; no evita la punción lumbar.'
  - texto: Sin efecto discriminativo
    correcta: false
    feedback: 'La fuente clasifica este hallazgo como «LR no medido». LR no medido Población: pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR. Motivo: la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí. Interpretación registrada: una prueba negativa no excluye la meningitis; no evita la punción lumbar.'
---

# Meningitis aguda

Hallazgos, cocientes documentados y límites de la evidencia.

## Nombre en inglés

Acute meningitis

## Códigos

Snomed: 822031000000101; Cie10: G03.9

## Hallazgos clínicos

### Acentuación de la cefalea con la sacudida cefálica (HM:3006)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR no medido

**Sensibilidad:** 0.653

**Ic95 sensibilidad:** 0.373 / 0.856

**Especificidad:** 0.704

**Ic95 especificidad:** 0.477 / 0.861

**Población:** pacientes con sospecha de meningitis en urgencias, 9 estudios y 1161 participantes; patrón de referencia, la pleocitosis en el LCR

**Referencia:** pmid:32524581

**Motivo:** la revisión publica sensibilidad y especificidad agrupadas, con certeza muy baja, pero no el cociente. No se calcula aquí

**Nota:** sin alteración de la conciencia (8 estudios, 921 participantes), Se 0.752 (IC95% 0.543-0.886) y Sp 0.608 (IC95% 0.434-0.759). Sustituye al LR+ 2.2 y LR− 0 de Attia 1999 (pmid:10411200), que venían de un único estudio de 1991

**Decisión:** una prueba negativa no excluye la meningitis; no evita la punción lumbar

### Cefalea (HM:0207)

**Rol:** Manifestación

**Estado del LR:** LR no medido

**Sensibilidad:** 0.5

**Ic95 sensibilidad:** 0.32 / 0.68

**Ref rendimiento:** pmid:10411200

**Motivo:** la fuente publica sensibilidad agrupada pero no especificidad, así que el cociente no es calculable desde el abstract

### Náuseas (HM:0301)

**Rol:** Manifestación

**Estado del LR:** LR no medido

**Sensibilidad:** 0.3

**Ic95 sensibilidad:** 0.22 / 0.38

**Ref rendimiento:** pmid:10411200

**Motivo:** sensibilidad agrupada sin especificidad; LR no calculable

### Vómitos (HM:0302)

**Rol:** Manifestación

**Estado del LR:** LR no medido

**Sensibilidad:** 0.3

**Ic95 sensibilidad:** 0.22 / 0.38

**Ref rendimiento:** pmid:10411200

**Motivo:** la fuente agrupa náuseas y vómitos en una sola estimación

### Fiebre (HM:0101)

**Rol:** Prueba sensible

**Estado del LR:** LR no medido

**Motivo:** forma parte de la tríada fiebre + rigidez de nuca + alteración del estado mental, cuya presencia de al menos uno tiene sensibilidad del 99-100%. La fuente no desglosa el cociente de cada componente por separado.

### Rigidez de nuca (HM:3005)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR medido

**Sensibilidad:** 0.3

**LR positivo:** Valor: 0.94; Referencia: pmid:12060874; Población: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR

**Referencia:** pmid:12060874

**Nota:** Attia 1999 (pmid:10411200) no publica su cociente aislado; este es de Thomas 2002. La fuente solo le halla valor en los 4 pacientes con ≥ 1000 leucocitos en el LCR

### Signo de Kernig (HM:3238)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR medido

**Sensibilidad:** 0.05

**LR positivo:** Valor: 0.97; Referencia: pmid:12060874; Población: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR

**Referencia:** pmid:12060874

### Signo de Brudzinski (HM:3239)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR medido

**Sensibilidad:** 0.05

**LR positivo:** Valor: 0.97; Referencia: pmid:12060874; Población: 297 adultos con sospecha de meningitis explorados antes de la punción lumbar; meningitis definida como ≥ 6 leucocitos en el LCR

**Referencia:** pmid:12060874

### Fontanela anterior abombada (HM:3240)

**Rol:** Apoyo diagnóstico

**Estado del LR:** LR medido

**LR positivo:** Valor: 3.5; IC del 95 %: 2.0 / 6.0; Referencia: pmid:20974781; Población: niños (revisión sistemática de 10 estudios prospectivos) con meningitis bacteriana confirmada en laboratorio frente a niños sin ella; hallazgo en la exploración

**Referencia:** pmid:20974781

**Nota:** Curtis 2010 publica además un LR 8.00 (IC95% 2.4-26) cuando el abombamiento se obtiene por la historia (referido por quien cuida al niño), distinto del hallazgo explorado. La fuente no publica LR− para este signo, y concluye que ningún signo aislado es diagnóstico

**Decisión:** aumenta la probabilidad de meningitis bacteriana en el niño; no la confirma y su ausencia no la descarta

### Alteración del nivel de conciencia (HM:0501)

**Rol:** Prueba sensible

**Estado del LR:** LR no medido

**Motivo:** componente de la tríada; la fuente no publica su cociente aislado

## Reglas clínicas

Nombre: Ausencia de la tríada clásica; Componentes: Fiebre / Rigidez de nuca / Alteración del nivel de conciencia; Criterio: ninguno de los tres presente; Sensibilidad de la presencia: 0.99 / 1.0; Referencia: pmid:10411200; Decisión: la ausencia simultánea de fiebre, rigidez de nuca y alteración del estado mental descarta la meningitis en la práctica; Advertencia: la fuente matiza que ante alto riesgo clínico hay que ir directamente a la punción lumbar, sin apoyarse en la exploración

## Aspectos pendientes de documentación

Decisión clínica (2026-10-31): la arista de la fontanela abombada (pmid:20974781) es pediátrica y su patrón de referencia es la meningitis bacteriana; las demás se midieron en adultos con «meningitis aguda». Si el responsable clínico prefiere no mezclar poblaciones en una condición, la alternativa es acuñar una condición propia («Meningitis bacteriana en el niño») y mover esa arista.

Sin probabilidad_base: Attia 1999 no publica prevalencia, y los resúmenes de Thomas 2002 y de Iguchi 2020 tampoco.

## Referencias y procedencia

**pmid:10411200:** The rational clinical examination. Does this adult patient have acute meningitis?. JAMA, 1999. DOI: 10.1001/jama.282.2.175.

**pmid:12060874:** The diagnostic accuracy of Kernig's sign, Brudzinski's sign, and nuchal rigidity in adults with suspected meningitis. Clin Infect Dis, 2002. DOI: 10.1086/340979.

**pmid:20974781:** Clinical features suggestive of meningitis in children: a systematic review of prospective data. Pediatrics, 2010. DOI: 10.1542/peds.2010-0277.

**pmid:32524581:** Diagnostic test accuracy of jolt accentuation for headache in acute meningitis in the emergency setting. Cochrane Database Syst Rev, 2020. DOI: 10.1002/14651858.CD012824.pub2.

Fuente clínica: medsemiotics-db, condición HM:6004.
