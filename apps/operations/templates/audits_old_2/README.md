# AUDIT a posteriori — Templating py4web / renoir

Refactoring des pages statiques en un layout de base + includes + design system
mutualisé.

## Arborescence (à recopier dans votre app py4web `myapp/`)

```
myapp/
├── templates/
│   ├── layout.html          ← layout de base (extends)
│   ├── _sidebar.html        ← include : barre latérale (état actif dynamique)
│   ├── _header.html         ← include : en-tête (Gestion / Session / Quitter)
│   ├── _footer.html         ← include : pied de page
│   ├── app.css              ← design system Tailwind (inliné par le layout)
│   ├── dashboard.html        ┐
│   ├── collecte.html         │
│   ├── ajout_operation.html  │
│   ├── modification_operation.html
│   ├── details.html          │ pages : [[extend 'layout.html']]
│   ├── comptes.html          │ + block title + block main + block js
│   ├── exercice.html         │
│   └── gestionnaire.html     ┘
└── static/
    └── js/app.js            ← JS global (nav, sous-menu, dropdowns en-tête)
```

## CSS / Tailwind v4 — IMPORTANT

Le runtime `@tailwindcss/browser` ne compile **que** les `<style type="text/tailwindcss">`
**inline**. Il n'ira PAS chercher une feuille liée par `<link>` : c'est pourquoi un
`<link ... href="app.css">` laisse les styles non appliqués (`@theme`, `@apply` et les
composants ne sont jamais générés).

**Solution retenue (dev, zéro build)** : `app.css` est placé dans `templates/` et le
layout l'inline ainsi :

```html
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
<style type="text/tailwindcss">
[[include 'app.css']]
</style>
```

`[[include 'app.css']]` insère le contenu du fichier (le CSS ne contient aucune balise
`[[ ]]`, donc renoir le passe tel quel) dans un bloc que le runtime compile bien. Vous
gardez **un seul fichier source** pour tout le design system.

**Prod (recommandé)** : compiler une fois avec la CLI Tailwind v4, lier le résultat et
retirer le runtime + le bloc inline :

```
npx @tailwindcss/cli -i templates/app.css -o static/css/app.build.css --watch
```
```html
<!-- en prod, dans layout.html, remplacer le bloc dev par : -->
<link rel="stylesheet" href="[[=URL('static', 'css/app.build.css')]]">
```

`app.css` contient : `@theme` (32 tokens), `@layer components` (toutes les classes :
`glass`, `nav-item`, `btn-*`, `field`, `utbl`, `status`, `act-btn`, `umodal`, `acc-*`,
`det-*`, `exo-*`, `combo-*`, `pill-*`…) puis le décor en CSS standard.

## Le layout

`layout.html` expose **3 blocks** :

- `[[block title]]` — titre de l'onglet (défaut : `AUDIT a posteriori`)
- `[[block main]]` — contenu central (`<main>`, barres d'action des formulaires, modales)
- `[[block js]]` — JavaScript propre à la page

Sidebar, header et footer sont des `[[include ...]]` : un seul endroit à modifier.

Chaque page :

```html
[[extend 'layout.html']]

[[block title]]Liste des comptes utilisateurs — AUDIT a posteriori[[end]]

[[block main]]
  <main class="glass ...">...</main>
  <!-- modales éventuelles -->
[[end]]

[[block js]]
<script> /* logique propre à la page */ </script>
[[end]]
```

## État actif de la navigation

La sidebar surligne l'élément courant via la variable **`active`**, passée par le
contrôleur. Valeurs : `dashboard`, `collecte`, `rapport`, `comptes`, `exercice`,
`gestionnaire`. Le sous-menu Administration s'ouvre automatiquement pour les trois
dernières. Sans `active`, pas de surlignage (aucune erreur).

```python
# controllers.py
from py4web import action, URL
from .common import session, db, auth

@action("dashboard")
@action.uses("dashboard.html", session, auth)
def dashboard():
    return dict(active="dashboard")

@action("comptes")
@action.uses("comptes.html", session, auth)
def comptes():
    return dict(active="comptes")        # → sous-menu Admin ouvert + « comptes » actif

# idem : collecte, rapport, exercice, gestionnaire, ajout_operation, modification_operation, details
```

Les liens utilisent `[[=URL('dashboard')]]`, `[[=URL('comptes')]]`, etc. — adaptez les
noms aux routes de vos `@action`.

## JS global vs. JS de page

`app.js` gère le commun (nav active, sous-menu, dropdowns en-tête) et expose
`window.closeAllDropdowns()`. Chaque page ne garde dans son `block js` que sa logique
propre. **`collecte`** gère sa propre navigation (comboboxes entrelacées) : son block js
pose `window.AUDIT_PAGE_OWNS_NAV = true;`, ce qui désactive `app.js` pour cette page.

## Note de rendu

Ces fichiers contiennent des balises renoir `[[ ... ]]` : ils se rendent **via py4web**,
pas en ouvrant le `.html` directement dans le navigateur.