# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import api, models
class IrUiMenu(models.Model):
    """Apply dynamic Flight School menu policies after native Odoo visibility checks."""

    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible_menu_ids = super()._visible_menu_ids(debug=debug)
        if self.env.su:
            return visible_menu_ids
        menus = self.browse(list(visible_menu_ids))
        policy_visible_menus = self.env['fs.access.service'].visible_menus(self.env.user, menus)
        return frozenset(policy_visible_menus.ids)
