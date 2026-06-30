# -*- coding: utf-8 -*-
"""Test de DEV : rend la chaîne complète des gabarits (per-mode -> layout ->
partiels) en hors-ligne, pour détecter toute erreur de syntaxe/structure yatl."""
import os, sys
sys.path.insert(0, 'apps')
import operations  # noqa: E402  (charge db + modes)
from operations.controllers import audit_controler as E  # noqa: E402
from operations.common import db  # noqa: E402
from yatl import render  # noqa: E402
from yatl.helpers import XML  # noqa: E402

TPL = os.path.join('apps', 'operations', 'templates')


def fake_URL(*parts, **kw):
    return '/' + '/'.join(str(p) for p in parts)


class _Resp:
    def __init__(self):
        self.body = ''

    def write(self, s, escape=True):
        s = '' if s is None else str(s)
        if hasattr(self.body, 'write'):
            self.body.write(s)
        else:
            self.body += s


def _base():
    return dict(URL=fake_URL, XML=XML, request=None, response=_Resp(), T=lambda s: s,
                current_user=None, active='collecte', globals=globals)


def render_tpl(rel, ctx):
    with open(os.path.join(TPL, rel), encoding='utf-8') as fh:
        src = fh.read()
    c = _base()
    c.update(ctx)
    return render(src, path=TPL, context=c, delimiters='[[ ]]')


ok = True
for mode, slug in (('AOO', 'aoo'), ('AOR_PI', 'aor_pi'), ('AOR_FT', 'aor_ft'), ('GAG', 'gag')):
    # ajout (create) + modification (edit) need a row -> create a temp one
    oid = E.create_operation(mode, {})
    try:
        for page, ctxbuilder in (
            ('ajout', lambda: E.form_context(mode)),
            ('modification', lambda: E.form_context(mode, oid)),
            ('details', lambda: E.details_context(mode, oid)),
        ):
            ctx = ctxbuilder()
            html = render_tpl('audits/%s/%s.html' % (slug, page), ctx)
            print('  OK %-7s %-12s -> %d chars' % (mode, page, len(html)))
    except Exception as e:
        ok = False
        import traceback
        print('  FAIL %s %s: %s' % (mode, page, e))
        traceback.print_exc()
    finally:
        E.soft_delete_operation(mode, oid)

print('ALL TEMPLATES RENDER OK' if ok else 'TEMPLATE ERRORS ABOVE')
