# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Refresh stored compliance values when upgrading from the stale version."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['fs.person']._recompute_compliance_statuses(full=True)
