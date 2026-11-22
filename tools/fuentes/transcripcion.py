"""Transcripción no canónica (.txt convertido del .doc) → una ficha YAML por capítulo.

Uso: a_yaml.py TXT DOC CARPETA_SALIDA

Decisión del editor (22-nov-2026): sin preliminares (prólogos, coautores, dedicatorias), sin los
capítulos de autores ajenos a la familia (XI y XXII) y sin firmas. Un capítulo firmado en la
fuente por otra persona que no es el autor fundador se marca sin nombrarla, para que nunca se
cite como legado suyo."""
import hashlib, re, sys
from pathlib import Path
import yaml

txt, doc, salida = map(Path, sys.argv[1:4])
EXCLUIDOS = {"XI", "XXII"}  # capítulos de autores ajenos a la familia
lineas = txt.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
CAP = re.compile(r"^\s*CAPITULO\s+([IVXL]+)\s*$")
ROMANOS = {"I":1,"V":5,"X":10,"L":50}
def arabigo(r):
    t=0
    for a,b in zip(r, r[1:]+" "):
        v=ROMANOS[a]; t += -v if b!=" " and ROMANOS[b]>v else v
    return t

ini_bib = next(i for i,l in enumerate(lineas) if l.strip()=="BIBLIOGRAFIA")
cuerpo, bib = lineas[:ini_bib], lineas[ini_bib+1:]
marcas = [(i, m[1]) for i,l in enumerate(cuerpo) if (m:=CAP.match(l))]
FIRMA = re.compile(r"^(Por\s+.+|Basil T\. Darras.*|Dra?\.\s+\S.*Torres Guerrero\.?)$")

def limpiar(bloque):
    texto = "\n".join(l.rstrip() for l in bloque).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", texto) + "\n"

caps = []
for k,(i,rom) in enumerate(marcas):
    fin = marcas[k+1][0] if k+1 < len(marcas) else len(cuerpo)
    bloque = [l for l in cuerpo[i+1:fin]]
    no_vacias = [j for j,l in enumerate(bloque) if l.strip()]
    titulo, firma = None, None
    j0 = no_vacias[0]
    if not FIRMA.match(bloque[j0].strip()):
        titulo = bloque[j0].strip(); bloque = bloque[j0+1:]
    nv = [j for j,l in enumerate(bloque) if l.strip()]
    if nv and FIRMA.match(bloque[nv[0]].strip()):
        firma = bloque[nv[0]].strip(); bloque = bloque[nv[0]+1:]
    caps.append({"numero": arabigo(rom), "romano": rom, "titulo_en_la_fuente": titulo,
                 "autoria_distinta_del_autor_fundador": firma is not None,
                 "citable_como_legado": firma is None,
                 "texto": limpiar(bloque), "bibliografia": []})

por_rom = {c["romano"]: c for c in caps}
actual = None
for l in bib:
    if (m := CAP.match(l)): actual = por_rom.get(m[1]); continue
    s = re.sub(r"^\s*\d+\.\s*", "", l).strip()
    if s and actual is not None: actual["bibliografia"].append(s)

comun = {
    "obra": "Neurología Pediátrica",
    "edicion_declarada_en_la_fuente": "3ra. EDICION",
    "canonica": False,
    "uso": ("Referencia de trabajo, no texto del libro: las lecciones se escriben desde cero. "
            "Un pasaje solo se cita como legado tras contrastarlo con la fotografía del impreso."),
    "procedencia": {
        "formato_original": "Microsoft Word 97-2003 (.doc)",
        "sha256_original": hashlib.sha256(doc.read_bytes()).hexdigest(),
        "conversion": "LibreOffice --convert-to txt (UTF-8); sin figuras, tablas ni paginación",
    },
    "advertencias": [
        "Sin números de página: las páginas de cada pasaje salen de las fotografías.",
        "Sin figuras ni tablas del impreso; algunas tablas quedaron como texto corrido.",
        "Con errores de transcripción (ortografía, nombres, acentos) que aquí no se corrigen.",
    ],
}

class Bloque(str): pass
yaml.add_representer(Bloque, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"), Dumper=yaml.SafeDumper)
def marcar(o):
    if isinstance(o, dict): return {k: marcar(v) for k,v in o.items()}
    if isinstance(o, list): return [marcar(v) for v in o]
    if isinstance(o, str) and "\n" in o: return Bloque(o)
    return o
def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "sin-titulo").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:50].rstrip("-")

salida.mkdir(parents=True, exist_ok=True)
escritos = 0
for c in caps:
    if c["romano"] in EXCLUIDOS:
        continue
    # Sin título en la fuente: el nombre del archivo toma su primer encabezado, el YAML no lo inventa.
    base = c["titulo_en_la_fuente"] or re.sub(r"^\d+\.\s*", "", c["texto"].strip().split("\n")[0])
    nombre = f"cap-{c['numero']:02d}-{slug(base)}.yaml"
    cab = (f"# Capítulo {c['romano']} de una transcripción NO CANÓNICA de «Neurología Pediátrica».\n"
           "# Referencia para el flujo de lecciones; se contrasta con las fotografías del impreso.\n"
           "# Generado con a_yaml.py; no se edita a mano.\n")
    (salida / nombre).write_text(cab + yaml.dump(marcar({**comun, "capitulo": c}), Dumper=yaml.SafeDumper,
                                 allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    escritos += 1
print(escritos, "fichas en", salida)
