# -*- coding: utf-8 -*-
"""Outil de DEV : crée les gabarits PROPRES à chaque mode (ajout / modification /
details) sous templates/audits/<slug>/. Chaque fichier inclut un partiel partagé
mais reste le point d'entrée du mode (personnalisable indépendamment)."""
import os

GEN = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(os.path.dirname(GEN)), 'templates', 'audits')

MODES = {
    'aoo': 'AOO — Appel d\'offres ouvert',
    'aor_pi': 'AOR_PI — Appel d\'offres restreint, prestations intellectuelles',
    'aor_ft': 'AOR_FT — Appel d\'offres restreint, fournitures & travaux',
    'gag': 'GAG — Gré à gré',
}

PAGES = {
    'ajout': ("Ajout d'une opération", '_operation_form_body.html', '_operation_form_js.html'),
    'modification': ("Modification d'une opération", '_operation_form_body.html', '_operation_form_js.html'),
    'details': ("Détails de l'opération", '_details_body.html', '_details_js.html'),
}

TMPL = """[[# Gabarit {page} PROPRE au mode {desc} — inclut un partiel partagé, personnalisable par mode. ]]
[[extend 'audits/layout.html']]

[[block title]]{title} [[=mode]] — AUDIT a posteriori[[end]]

[[block main]]
[[include 'audits/{body}']]
[[end]]

[[block js]]
[[include 'audits/{js}']]
[[end]]
"""

for slug, desc in MODES.items():
    d = os.path.join(TPL, slug)
    os.makedirs(d, exist_ok=True)
    for page, (title, body, js) in PAGES.items():
        out = os.path.join(d, page + '.html')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(TMPL.format(page=page, desc=desc, title=title, body=body, js=js))
        print('written', os.path.relpath(out, TPL))
