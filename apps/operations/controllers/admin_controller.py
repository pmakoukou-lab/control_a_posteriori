from py4web import action

from ..common import (
    auth,
    db,
    flash,
    session,
)

from ..fixtures.rbac_fixture import access

@action('admin/dashboard', method=['GET', 'POST'])
@action.uses('admin/dashboard_v3.html', db, session, auth, flash, access(roles='Administrateur'))
def dashboard_index():
    return dict(page='index')

@action('admin/dashboard/<name>', method=['GET', 'POST'])
@action.uses('admin/dashboard_v3.html', db, session, auth, flash, access(roles='Administrateur'))
def dashboard(name):
    return dict(page=name)

@action('admin/users/add', method=['POST'])
@action.uses(db, session, auth, flash)
def add_user():
    pass


@action('admin/group/add', method=['POST'])
@action.uses(db, session, auth, flash)
def add_group():
    pass


@action('admin/permission/add', method=['POST'])
@action.uses(db, session, auth, flash)
def add_permission():
    pass