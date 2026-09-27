import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import statistiques  # noqa: E402


def depot(etoiles, langages):
    return {"stargazerCount": etoiles,
            "languages": {"edges": [{"size": taille, "node": {"name": nom, "color": couleur}}
                                    for nom, taille, couleur in langages]}}


def page(depots, suivante=None):
    return {
        "contributionsCollection": {"totalCommitContributions": 321, "contributionCalendar": {"totalContributions": 1234}},
        "pullRequests": {"totalCount": 12},
        "repositories": {"totalCount": 3, "pageInfo": {"hasNextPage": suivante is not None, "endCursor": suivante},
                         "nodes": depots},
    }


PAGES = {
    None: page([depot(2, [("Python", 6000, "#3572A5"), ("Jupyter Notebook", 900000, "#DA5B0B")]),
                depot(1, [("HTML", 2000, "#e34c26")])], suivante="curseur1"),
    "curseur1": page([depot(0, [("Python", 2000, "#3572A5"), ("A<B & C", 0, None)])]),
}


def faux_interroger(login, jeton, apres=None):
    assert login == "Olaffson" and jeton == "jeton"
    return PAGES[apres]


@pytest.fixture
def stats():
    return statistiques.calculer(statistiques.recuperer("Olaffson", "jeton", faux_interroger))


def test_toutes_les_pages_sont_recuperees():
    assert len(statistiques.recuperer("Olaffson", "jeton", faux_interroger)) == 2


def test_statistiques(stats):
    assert stats["depots"] == 3
    assert stats["etoiles"] == 3
    assert stats["commits"] == 321
    assert stats["contributions"] == 1234
    assert stats["pull_requests"] == 12


def test_langages(stats):
    noms = [l["nom"] for l in stats["langages"]]
    assert noms[:2] == ["Python", "HTML"]
    # les notebooks sont ignorés : ils occuperaient toute la barre
    assert "Jupyter Notebook" not in noms
    assert stats["langages"][0]["part"] == pytest.approx(0.8)
    assert sum(l["part"] for l in stats["langages"]) == pytest.approx(1)


def test_langages_regroupes_au_dela_du_maximum(monkeypatch):
    monkeypatch.setattr(statistiques, "NB_LANGAGES", 1)
    stats = statistiques.calculer(statistiques.recuperer("Olaffson", "jeton", faux_interroger))
    assert [l["nom"] for l in stats["langages"]] == ["Python", "Autres"]
    assert stats["langages"][1]["part"] == pytest.approx(0.2)


@pytest.mark.parametrize("theme", statistiques.THEMES.values())
def test_cartes_svg_valides(stats, theme):
    for svg in (statistiques.carte_stats(stats, theme), statistiques.carte_langages(stats, theme),
                statistiques.carte_attente("Titre", theme)):
        racine = ET.fromstring(svg)
        assert racine.tag.endswith("svg")


def test_texte_echappe(stats):
    svg = statistiques.carte_langages(stats, statistiques.THEMES["clair"])
    assert "A&lt;B &amp; C" in svg
    assert "321" in statistiques.carte_stats(stats, statistiques.THEMES["clair"])


def test_separateur_des_milliers():
    assert statistiques._nombre(1234) == "1 234"


def test_aucun_langage():
    stats = statistiques.calculer([page([depot(0, [("Jupyter Notebook", 5000, "#DA5B0B")])])])
    assert stats["langages"] == []
    svg = statistiques.carte_langages(stats, statistiques.THEMES["sombre"])
    ET.fromstring(svg)
    assert "Aucun langage" in svg
