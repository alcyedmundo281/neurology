import json
from pathlib import Path

import yaml


def test_la_licencia_y_la_autoria_de_catalogo_coinciden_con_la_obra():
    raiz = Path(__file__).resolve().parents[2]
    cita = yaml.safe_load((raiz / "CITATION.cff").read_text(encoding="utf-8"))
    zenodo = json.loads((raiz / ".zenodo.json").read_text(encoding="utf-8"))
    mapa = yaml.safe_load((raiz / "lecciones/mapa.yaml").read_text(encoding="utf-8"))

    licencia = cita["license"]
    assert licencia == zenodo["license"] == "CC-BY-NC-SA-4.0"
    titulares = (raiz / "LICENSE").read_text(encoding="utf-8")
    assert licencia in titulares
    assert cita["title"] == zenodo["title"] == mapa["obra"]["titulo"]

    personas = list(mapa["personas"].values())
    assert len(personas) == len(cita["authors"]) == len(zenodo["creators"]) == 5
    for persona, autor, creador in zip(personas, cita["authors"], zenodo["creators"], strict=True):
        nombre = autor["given-names"]
        apellido = autor["family-names"]
        assert persona["nombre"] == f"{nombre} {apellido}"
        assert persona["nombre"] in titulares
        assert creador["name"] == f"{apellido}, {nombre}"
        if orcid := persona.get("orcid"):
            assert persona["nombre"] == "Alcy Edmundo Torres Guerrero"
            assert orcid == creador["orcid"] == "0000-0002-9742-375X"
            assert autor["orcid"] == f"https://orcid.org/{orcid}"
        else:
            assert "orcid" not in autor and "orcid" not in creador

    assert "orcid" not in personas[0]
    assert [p["orcid"] for p in (personas[1], personas[2], personas[4])] == [None, None, None]
    assert sum("orcid" in a for a in cita["authors"]) == 1
    assert "doi" not in cita and "doi" not in zenodo
    assert "publisher" not in zenodo and "isbn" not in zenodo
