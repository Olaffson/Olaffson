"""
Génère la bannière animée de la page d'accueil (assets/banniere-clair.svg et banniere-sombre.svg).

Le nom s'affiche au-dessus d'une ligne où les rôles s'écrivent puis s'effacent l'un après l'autre,
comme tapés au clavier. Pour changer le texte, modifier NOM et ROLES puis lancer :

    python scripts/banniere.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

NOM = "Olivier Kotwica"
ROLES = [
    "Data Analyst / Data Engineer",
    "Python · SQL · Azure",
    "Scraping, ML et MLOps",
]

LARGEUR, HAUTEUR = 900, 220
TAILLE_ROLE = 26
# largeur moyenne d'un caractère d'une police à chasse fixe, en proportion de la taille de police
CHASSE = 0.6
DUREE_ROLE = 4.0  # secondes pendant lesquelles chaque rôle est tapé, affiché puis effacé

THEMES = {
    "clair": {"fond1": "#e0ecff", "fond2": "#f5e8ff", "nom": "#1f2937", "role": "#2563eb", "vague": "#c7dbff"},
    "sombre": {"fond1": "#0d1b2a", "fond2": "#1b1035", "nom": "#f3f4f6", "role": "#60a5fa", "vague": "#1e3a5f"},
}


def _animation_role(indice: int, nb_roles: int, largeur_texte: float) -> tuple[str, str]:
    """
    Valeurs SMIL (keyTimes, values) de la largeur visible d'un rôle sur un cycle complet.

    Pendant sa part du cycle, le rôle est tapé (0 → largeur), reste affiché, puis est effacé.
    """
    part = 1 / nb_roles
    debut = indice * part
    temps = [0, debut, debut + part * 0.35, debut + part * 0.8, debut + part * 0.95, 1]
    largeurs = [0, 0, largeur_texte, largeur_texte, 0, 0]
    # des keyTimes identiques successifs sont autorisés mais doivent rester croissants
    return ";".join(f"{t:.4f}" for t in temps), ";".join(f"{l:.1f}" for l in largeurs)


def generer(theme: dict) -> str:
    """Renvoie le code SVG de la bannière pour un thème de couleurs."""
    duree = DUREE_ROLE * len(ROLES)
    x_role = LARGEUR / 2
    y_role = 150
    roles_svg = []
    for i, role in enumerate(ROLES):
        largeur_texte = len(role) * TAILLE_ROLE * CHASSE
        x_debut = x_role - largeur_texte / 2
        temps, largeurs = _animation_role(i, len(ROLES), largeur_texte)
        roles_svg.append(f"""
  <clipPath id="masque{i}">
    <rect x="{x_debut:.1f}" y="{y_role - TAILLE_ROLE}" width="0" height="{TAILLE_ROLE * 1.4:.0f}">
      <animate attributeName="width" dur="{duree}s" repeatCount="indefinite" keyTimes="{temps}" values="{largeurs}"/>
    </rect>
  </clipPath>
  <text class="role" x="{x_debut:.1f}" y="{y_role}" clip-path="url(#masque{i})">{escape(role)}</text>
  <rect class="curseur" x="{x_debut:.1f}" y="{y_role - TAILLE_ROLE + 2}" width="3" height="{TAILLE_ROLE + 4}" opacity="0">
    <animate attributeName="x" dur="{duree}s" repeatCount="indefinite" keyTimes="{temps}"
             values="{';'.join(f'{x_debut + float(l):.1f}' for l in largeurs.split(';'))}"/>
    <animate attributeName="opacity" dur="{duree}s" repeatCount="indefinite" calcMode="discrete"
             keyTimes="0;{i / len(ROLES):.4f};{(i + 1) / len(ROLES):.4f}" values="0;1;0"/>
  </rect>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{LARGEUR}" height="{HAUTEUR}" viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" aria-labelledby="titre">
  <title id="titre">{escape(NOM)} : {escape(', '.join(ROLES))}</title>
  <style>
    .nom {{ font: 700 44px 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; fill: {theme['nom']}; }}
    .role {{ font: 500 {TAILLE_ROLE}px Consolas, 'Courier New', monospace; fill: {theme['role']}; }}
    .curseur {{ fill: {theme['role']}; animation: clignote 0.9s steps(1) infinite; }}
    @keyframes clignote {{ 50% {{ fill-opacity: 0; }} }}
    .vague {{ fill: {theme['vague']}; opacity: 0.6; animation: flotte 8s ease-in-out infinite alternate; }}
    @keyframes flotte {{ to {{ transform: translateX(-60px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .vague, .curseur {{ animation: none; }} }}
  </style>
  <defs>
    <clipPath id="carte"><rect width="{LARGEUR}" height="{HAUTEUR}" rx="16"/></clipPath>
    <linearGradient id="fond" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{theme['fond1']}"/>
      <stop offset="1" stop-color="{theme['fond2']}"/>
    </linearGradient>
  </defs>
  <rect width="{LARGEUR}" height="{HAUTEUR}" rx="16" fill="url(#fond)"/>
  <path class="vague" clip-path="url(#carte)" d="M0 185 C 150 150, 300 215, 450 185 S 750 150, 960 185 L 960 {HAUTEUR} L 0 {HAUTEUR} Z"/>
  <text class="nom" x="{LARGEUR / 2}" y="92" text-anchor="middle">{escape(NOM)}</text>{''.join(roles_svg)}
</svg>
"""


if __name__ == "__main__":
    dossier = Path(__file__).parent.parent / "assets"
    dossier.mkdir(exist_ok=True)
    for nom_theme, theme in THEMES.items():
        (dossier / f"banniere-{nom_theme}.svg").write_text(generer(theme), encoding="utf-8")
        print(f"assets/banniere-{nom_theme}.svg")
