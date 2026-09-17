# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


RETIRED_ACCESS_XMLIDS = (
    'access_fs_scheduling_wizard_user',
    'access_fs_scheduling_wizard_line_user',
    'access_fs_scheduling_wizard_bulk_action_user',
)


def migrate(cr, version):
    """Remove base-user ACLs superseded by instructor scheduling wizard ACLs."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    external_ids = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_scheduling'),
        ('name', 'in', RETIRED_ACCESS_XMLIDS),
        ('model', '=', 'ir.model.access'),
    ])
    access_rules = env['ir.model.access'].sudo().browse(external_ids.mapped('res_id')).exists()
    access_rules.unlink()
    external_ids.unlink()
