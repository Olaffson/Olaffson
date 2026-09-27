"""
Génère les cartes de statistiques GitHub de la page d'accueil, en version claire et sombre :
- assets/stats-{clair,sombre}.svg : dépôts, étoiles, commits, contributions, pull requests ;
- assets/langages-{clair,sombre}.svg : langages les plus utilisés dans les dépôts publics.

Lancé chaque jour par la GitHub Action .github/workflows/statistiques.yml. En local :

    GITHUB_TOKEN=<jeton> python scripts/statistiques.py <login>

Avec --attente, génère des cartes « en cours de génération » sans interroger GitHub.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com/graphql"
DOSSIER = Path(__file__).parent.parent / "assets"

# Les notebooks comptent aussi leurs sorties (tableaux, images) : leur taille ne reflète pas le code
# écrit et ils occuperaient presque toute la barre. Retirer un langage de cette liste pour le compter.
LANGAGES_IGNORES = {"Jupyter Notebook"}
NB_LANGAGES = 6

THEMES = {
    "clair": {"fond": "#ffffff", "bordure": "#d0d7de", "texte": "#1f2328", "discret": "#59636e", "titre": "#2563eb"},
    "sombre": {"fond": "#0d1117", "bordure": "#30363d", "texte": "#e6edf3", "discret": "#9198a1", "titre": "#60a5fa"},
}
LARGEUR, HAUTEUR = 440, 200
POLICE = "'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif"

REQUETE = """
query($login: String!, $apres: String) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions }
    }
    pullRequests { totalCount }
    repositories(first: 100, after: $apres, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def interroger(login: str, jeton: str, apres: str | None = None) -> dict:
    """Envoie la requête GraphQL pour une page de dépôts."""
    corps = json.dumps({"query": REQUETE, "variables": {"login": login, "apres": apres}}).encode()
    requete = urllib.request.Request(API, data=corps, headers={"Authorization": f"bearer {jeton}"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        resultat = json.load(reponse)
    if resultat.get("errors"):
        raise RuntimeError(f"Erreur de l'API GitHub : {resultat['errors']}")
    return resultat["data"]["user"]


def recuperer(login: str, jeton: str, interroger=interroger) -> list[dict]:
    """Récupère toutes les pages de dépôts de l'utilisateur."""
    pages, apres = [], None
    while True:
        page = interroger(login, jeton, apres)
        pages.append(page)
        infos = page["repositories"]["pageInfo"]
        if not infos["hasNextPage"]:
            return pages
        apres = infos["endCursor"]


def calculer(pages: list[dict]) -> dict:
    """Calcule les statistiques affichées à partir des réponses de l'API."""
    premiere = pages[0]
    depots = [depot for page in pages for depot in page["repositories"]["nodes"]]

    tailles, couleurs = {}, {}
    for depot in depots:
        for arete in depot["languages"]["edges"]:
            nom = arete["node"]["name"]
            if nom in LANGAGES_IGNORES:
                continue
            tailles[nom] = tailles.get(nom, 0) + arete["size"]
            couleurs[nom] = arete["node"]["color"] or "#8b949e"

    total = sum(tailles.values()) or 1  # évite une division par zéro s'il n'y a aucun langage
    classement = sorted(tailles.items(), key=lambda x: -x[1])
    langages = [{"nom": nom, "part": taille / total, "couleur": couleurs[nom]} for nom, taille in classement[:NB_LANGAGES]]
    reste = sum(taille for _, taille in classement[NB_LANGAGES:])
    if reste:
        langages.append({"nom": "Autres", "part": reste / total, "couleur": "#8b949e"})

    return {
        "depots": premiere["repositories"]["totalCount"],
        "etoiles": sum(depot["stargazerCount"] for depot in depots),
        "commits": premiere["contributionsCollection"]["totalCommitContributions"],
        "contributions": premiere["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "pull_requests": premiere["pullRequests"]["totalCount"],
        "langages": langages,
    }


def _carte(titre: str, contenu: str, theme: dict, description: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{LARGEUR}" height="{HAUTEUR}" viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" aria-labelledby="titre desc">
  <title id="titre">{escape(titre)}</title>
  <desc id="desc">{escape(description)}</desc>
  <style>
    text {{ font-family: {POLICE}; }}
    .titre {{ font-size: 18px; font-weight: 600; fill: {theme['titre']}; }}
    .libelle {{ font-size: 14px; fill: {theme['discret']}; }}
    .valeur {{ font-size: 14px; font-weight: 600; fill: {theme['texte']}; }}
    .apparait {{ opacity: 0; animation: apparait 0.5s ease-out forwards; }}
    @keyframes apparait {{ to {{ opacity: 1; }} }}
    .barre {{ transform-box: fill-box; transform: scaleX(0); animation: grandit 0.8s ease-out forwards; }}
    @keyframes grandit {{ to {{ transform: scaleX(1); }} }}
    @media (prefers-reduced-motion: reduce) {{ .apparait, .barre {{ animation: none; opacity: 1; transform: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{LARGEUR - 1}" height="{HAUTEUR - 1}" rx="10" fill="{theme['fond']}" stroke="{theme['bordure']}"/>
  <text class="titre" x="25" y="36">{escape(titre)}</text>
{contenu}
</svg>
"""


def carte_stats(stats: dict, theme: dict) -> str:
    lignes = [
        ("Dépôts publics", stats["depots"], "#2563eb"),
        ("Étoiles reçues", stats["etoiles"], "#eab308"),
        ("Commits (12 derniers mois)", stats["commits"], "#16a34a"),
        ("Contributions (12 derniers mois)", stats["contributions"], "#9333ea"),
        ("Pull requests", stats["pull_requests"], "#ea580c"),
    ]
    contenu = "\n".join(
        f"""  <g class="apparait" style="animation-delay: {0.15 * i:.2f}s">
    <circle cx="31" cy="{66 + 27 * i}" r="5" fill="{couleur}"/>
    <text class="libelle" x="45" y="{71 + 27 * i}">{escape(libelle)}</text>
    <text class="valeur" x="{LARGEUR - 25}" y="{71 + 27 * i}" text-anchor="end">{_nombre(valeur)}</text>
  </g>"""
        for i, (libelle, valeur, couleur) in enumerate(lignes))
    description = ", ".join(f"{libelle} : {valeur}" for libelle, valeur, _ in lignes)
    return _carte("Statistiques GitHub", contenu, theme, description)


def _nombre(valeur: int) -> str:
    """Nombre avec une espace fine comme séparateur des milliers (12 345)."""
    return f"{valeur:,}".replace(",", " ")


def carte_langages(stats: dict, theme: dict) -> str:
    x, largeur_barre, morceaux = 25, LARGEUR - 50, []
    for langage in stats["langages"]:
        largeur = langage["part"] * largeur_barre
        morceaux.append(f'<rect x="{x:.2f}" y="56" width="{largeur:.2f}" height="10" fill="{langage["couleur"]}"/>')
        x += largeur
    barre = f"""  <clipPath id="arrondi"><rect x="25" y="56" width="{largeur_barre}" height="10" rx="5"/></clipPath>
  <g clip-path="url(#arrondi)"><g class="barre">{''.join(morceaux)}</g></g>"""

    legende = []
    for i, langage in enumerate(stats["langages"]):
        colonne, ligne = i % 2, i // 2
        lx, ly = 25 + colonne * 200, 96 + ligne * 27
        legende.append(f"""  <g class="apparait" style="animation-delay: {0.3 + 0.1 * i:.2f}s">
    <circle cx="{lx + 6}" cy="{ly - 5}" r="5" fill="{langage['couleur']}"/>
    <text class="libelle" x="{lx + 18}" y="{ly}">{escape(langage['nom'])} <tspan class="valeur">{langage['part'] * 100:.1f} %</tspan></text>
  </g>""")
    if not stats["langages"]:
        legende.append('  <text class="libelle" x="25" y="110">Aucun langage détecté dans les dépôts publics</text>')
    description = ", ".join(f"{l['nom']} : {l['part'] * 100:.1f} %" for l in stats["langages"]) or "Aucun langage"
    return _carte("Langages les plus utilisés", barre + "\n" + "\n".join(legende), theme, description)


def carte_attente(titre: str, theme: dict) -> str:
    contenu = '  <text class="libelle" x="25" y="110">Statistiques en cours de génération…</text>'
    return _carte(titre, contenu, theme, "Statistiques en cours de génération")


def enregistrer(nom: str, svg: str) -> None:
    DOSSIER.mkdir(exist_ok=True)
    (DOSSIER / nom).write_text(svg, encoding="utf-8")
    print(f"assets/{nom}")


def main(arguments: list[str]) -> None:
    if "--attente" in arguments:
        for nom_theme, theme in THEMES.items():
            enregistrer(f"stats-{nom_theme}.svg", carte_attente("Statistiques GitHub", theme))
            enregistrer(f"langages-{nom_theme}.svg", carte_attente("Langages les plus utilisés", theme))
        return

    login = arguments[0] if arguments else os.environ["GITHUB_REPOSITORY_OWNER"]
    stats = calculer(recuperer(login, os.environ["GITHUB_TOKEN"]))
    for nom_theme, theme in THEMES.items():
        enregistrer(f"stats-{nom_theme}.svg", carte_stats(stats, theme))
        enregistrer(f"langages-{nom_theme}.svg", carte_langages(stats, theme))


if __name__ == "__main__":
    main(sys.argv[1:])
