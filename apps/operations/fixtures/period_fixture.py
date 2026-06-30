# -*- coding: utf-8 -*-
"""
Cadre **Gestion** (exercice budgétaire) / **Mission** (session budgétaire) actif.

Partagé par le tableau de bord et par le sélecteur de l'en-tête commun
(``_header.html``). Le choix actif est mémorisé dans la session py4web (cookie)
via la route ``set_period`` ; à défaut, on retombe sur le dernier exercice et sa
dernière mission.

La Fixture ``period`` injecte ``period`` (cadre actif + options) dans la sortie
des pages qui portent l'en-tête commun (à placer dans ``action.uses`` APRÈS ``db``
et ``session``).
"""
from py4web.core import Fixture

from ..common import db, session


def period_options():
    """Exercices (gestions) + leurs missions (sessions), pour le sélecteur.

    Renvoie une liste ``[{id, annee, label, sessions:[{id, num, label}]}]``,
    exercices triés du plus récent au plus ancien, missions dans l'ordre de saisie.
    """
    out = []
    exos = db(db.exercice_budgetaire.is_deleted == False).select(  # noqa: E712
        orderby=~db.exercice_budgetaire.annee)
    for e in exos:
        sess = db((db.session_budgetaire.exercice == e.id) &
                  (db.session_budgetaire.is_deleted == False)).select(  # noqa: E712
            orderby=db.session_budgetaire.id)
        out.append(dict(
            id=e.id, annee=e.annee, label=str(e.annee),
            sessions=[dict(id=s.id, num=i + 1, label="Mission %d" % (i + 1))
                      for i, s in enumerate(sess)],
        ))
    return out


def active_period(options=None):
    """Cadre actif (gestion/mission) lu dans la session py4web.

    Défaut : dernier exercice + sa dernière mission. Renvoie aussi ``options``
    pour alimenter le sélecteur. Tous les libellés sont prêts à l'affichage.
    """
    opts = options if options is not None else period_options()
    if not opts:
        return dict(gestion_id=None, session_id=None, session_num=None,
                    gestion_label="—", session_label="—", options=[])
    gid = session.get('period_gestion')
    sid = session.get('period_session')
    gestion = next((e for e in opts if e['id'] == gid), opts[0])
    sessions = gestion['sessions']
    sess = next((s for s in sessions if s['id'] == sid),
                (sessions[-1] if sessions else None))
    return dict(
        gestion_id=gestion['id'],
        gestion_label=gestion['label'],
        session_id=(sess['id'] if sess else None),
        session_num=(sess['num'] if sess else None),
        session_label=(sess['label'] if sess else "—"),
        options=opts,
    )


class Period(Fixture):
    """Injecte ``period`` (cadre Gestion/Mission actif + options) dans la sortie."""

    def on_success(self, context):
        output = context.get("output")
        if isinstance(output, dict) and "period" not in output:
            output["period"] = active_period()


period = Period()
