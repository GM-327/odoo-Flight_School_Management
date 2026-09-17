# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Remove the retired manager ACL for the global settings wizard."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    external_id = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_fleet'),
        ('name', '=', 'access_fs_fleet_res_config_settings_manager'),
        ('model', '=', 'ir.model.access'),
    ])
    access_rule = env['ir.model.access'].sudo().browse(external_id.res_id).exists()
    access_rule.unlink()
    external_id.exists().unlink()
