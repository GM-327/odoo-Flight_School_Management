# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


RETIRED_ACCESS_XMLIDS = (
    'access_fs_flight_cancel_wizard',
    'access_fs_add_flight_wizard',
    'access_fs_add_sim_wizard',
    'access_fs_flight_delete_wizard',
    'access_fs_import_schedule_wizard',
)


def migrate(cr, version):
    """Remove base-user ACLs superseded by manager-only operation wizards."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    external_ids = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_flights'),
        ('name', 'in', RETIRED_ACCESS_XMLIDS),
        ('model', '=', 'ir.model.access'),
    ])
    access_rules = env['ir.model.access'].sudo().browse(external_ids.mapped('res_id')).exists()
    access_rules.unlink()
    external_ids.unlink()
