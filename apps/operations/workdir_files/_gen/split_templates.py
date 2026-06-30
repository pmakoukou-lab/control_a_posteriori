# -*- coding: utf-8 -*-
"""Outil de DEV : découpe les gabarits partagés operation_form.html / details.html
en PARTIELS réutilisables (corps + js), inclus par les gabarits PROPRES à chaque
mode (templates/audits/<mode>/ajout|modification|details.html)."""
import os

GEN = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(os.path.dirname(GEN)), 'templates', 'audits')


def slice_lines(path, a, b):
    with open(path, encoding='utf-8') as fh:
        lines = fh.readlines()
    return ''.join(lines[a - 1:b])          # 1-based inclusive


def write(path, text):
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print('written', os.path.relpath(path, TPL))


form = os.path.join(TPL, 'operation_form.html')
det = os.path.join(TPL, 'details.html')

write(os.path.join(TPL, '_operation_form_body.html'), slice_lines(form, 6, 156))
write(os.path.join(TPL, '_operation_form_js.html'), slice_lines(form, 160, 505))
write(os.path.join(TPL, '_details_body.html'), slice_lines(det, 6, 64))
write(os.path.join(TPL, '_details_js.html'), slice_lines(det, 68, 101))
