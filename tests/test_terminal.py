import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import terminal  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"


@pytest.mark.parametrize("theme", terminal.THEMES.values())
def test_svg_valide_avec_une_ligne_par_phrase(theme):
    racine = ET.fromstring(terminal.generer(theme))
    textes = [t.text for t in racine.iter(f"{SVG}text") if "texte" in t.get("class", "")]
    assert textes == terminal.PHRASES


def test_phrases_tiennent_dans_la_fenetre():
    debut = 24 + len(terminal.INVITE) * terminal.TAILLE * terminal.CHASSE
    for phrase in terminal.PHRASES:
        assert debut + (len(phrase) + 1) * terminal.TAILLE * terminal.CHASSE < terminal.LARGEUR
