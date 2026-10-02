"""
Génère le terminal animé de la page d'accueil (assets/terminal-clair.svg et terminal-sombre.svg).

Une fenêtre de terminal affiche une invite de commande, après laquelle des phrases s'écrivent puis
s'effacent l'une après l'autre, comme tapées au clavier. Pour changer le texte, modifier PHRASES
puis lancer :

    python scripts/terminal.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

from banniere import CHASSE, _animation_role

INVITE = "olivier@data:~$ "
PHRASES = [
    "pip install café",
    "SELECT * FROM idees WHERE drole = TRUE;",
    "Bronze → Silver → Gold, comme aux JO",
    "git commit -m \"ça marche chez moi\"",
    "Je transforme des CSV en décisions",
]

LARGEUR, HAUTEUR = 900, 110
TAILLE = 22
DUREE_PHRASE = 4.0  # secondes pendant lesquelles chaque phrase est tapée, affichée puis effacée

THEMES = {
    "clair": {"fond": "#f6f8fa", "barre": "#e5e7eb", "bord": "#d0d7de", "invite": "#16a34a", "texte": "#1f2937"},
    "sombre": {"fond": "#0d1117", "barre": "#161b22", "bord": "#30363d", "invite": "#4ade80", "texte": "#e6edf3"},
}
# boutons de fenêtre façon macOS : fermer, réduire, agrandir
BOUTONS = ["#ff5f57", "#febc2e", "#28c840"]


def generer(theme: dict) -> str:
    """Renvoie le code SVG du terminal pour un thème de couleurs."""
    duree = DUREE_PHRASE * len(PHRASES)
    x_invite, y_ligne = 24, 78
    x_debut = x_invite + len(INVITE) * TAILLE * CHASSE
    phrases_svg = []
    for i, phrase in enumerate(PHRASES):
        largeur_texte = len(phrase) * TAILLE * CHASSE
        temps, largeurs = _animation_role(i, len(PHRASES), largeur_texte)
        phrases_svg.append(f"""
  <clipPath id="ligne{i}">
    <rect x="{x_debut:.1f}" y="{y_ligne - TAILLE}" width="0" height="{TAILLE * 1.4:.0f}">
      <animate attributeName="width" dur="{duree}s" repeatCount="indefinite" keyTimes="{temps}" values="{largeurs}"/>
    </rect>
  </clipPath>
  <text class="texte" x="{x_debut:.1f}" y="{y_ligne}" clip-path="url(#ligne{i})">{escape(phrase)}</text>
  <rect class="curseur" x="{x_debut:.1f}" y="{y_ligne - TAILLE + 3}" width="11" height="{TAILLE + 2}" opacity="0">
    <animate attributeName="x" dur="{duree}s" repeatCount="indefinite" keyTimes="{temps}"
             values="{';'.join(f'{x_debut + float(l):.1f}' for l in largeurs.split(';'))}"/>
    <animate attributeName="opacity" dur="{duree}s" repeatCount="indefinite" calcMode="discrete"
             keyTimes="0;{i / len(PHRASES):.4f};{(i + 1) / len(PHRASES):.4f}" values="0;1;0"/>
  </rect>""")

    boutons = "".join(f'\n  <circle cx="{20 + 20 * i}" cy="17" r="6" fill="{couleur}"/>'
                      for i, couleur in enumerate(BOUTONS))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{LARGEUR}" height="{HAUTEUR}" viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" aria-labelledby="titre">
  <title id="titre">{escape(' · '.join(PHRASES))}</title>
  <style>
    .invite, .texte {{ font: 500 {TAILLE}px Consolas, 'Courier New', monospace; }}
    .invite {{ fill: {theme['invite']}; }}
    .texte {{ fill: {theme['texte']}; }}
    .curseur {{ fill: {theme['texte']}; fill-opacity: 0.7; animation: clignote 0.9s steps(1) infinite; }}
    @keyframes clignote {{ 50% {{ fill-opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .curseur {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{LARGEUR - 1}" height="{HAUTEUR - 1}" rx="10" fill="{theme['fond']}" stroke="{theme['bord']}"/>
  <path d="M0.5 34 V10.5 a10 10 0 0 1 10 -10 H{LARGEUR - 10.5} a10 10 0 0 1 10 10 V34 Z" fill="{theme['barre']}"/>{boutons}
  <text class="invite" x="{x_invite}" y="{y_ligne}" xml:space="preserve">{escape(INVITE)}</text>{''.join(phrases_svg)}
</svg>
"""


if __name__ == "__main__":
    dossier = Path(__file__).parent.parent / "assets"
    dossier.mkdir(exist_ok=True)
    for nom_theme, theme in THEMES.items():
        (dossier / f"terminal-{nom_theme}.svg").write_text(generer(theme), encoding="utf-8")
        print(f"assets/terminal-{nom_theme}.svg")
