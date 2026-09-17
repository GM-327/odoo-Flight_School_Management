# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


RETIRED_ACCESS_XMLIDS = (
    'access_fs_training_dashboard_user',
    'access_fs_flight_mission_manager',
)


def migrate(cr, version):
    """Remove ACLs superseded by role-aligned replacements."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    external_ids = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_training'),
        ('name', 'in', RETIRED_ACCESS_XMLIDS),
        ('model', '=', 'ir.model.access'),
    ])
    access_rules = env['ir.model.access'].sudo().browse(external_ids.mapped('res_id')).exists()
    access_rules.unlink()
    external_ids.unlink()
