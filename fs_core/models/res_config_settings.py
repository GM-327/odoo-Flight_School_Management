# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Settings res config settings module.

Purpose:
    Defines classes ResConfigSettings for central settings, shared security groups, departments, and base configuration records.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: base, base_setup, auth_signup.
    All Flight School addons consume the groups, menu roots, and shared settings defined here.
"""
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


ICAO_CODE_PATTERN = re.compile(r'^[A-Z]{4}$')


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school core module.

    This is the base settings class that provides general settings.
    Other flight school modules extend this with their own settings.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        All Flight School addons consume the groups, menu roots, and shared settings defined here.
    """

    _inherit = 'res.config.settings'

    # === General Settings ===
    fs_default_home_base = fields.Char(
        string='Default Home Base',
        default='DTTI',
        config_parameter='flight_school.default_home_base',
        help="ICAO airport code used as the default home base for new aircraft.",
    )
    fs_default_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Default Country',
        config_parameter='flight_school.default_country_id',
        help="Default country/nationality for new students and pilots.",
    )

    @api.model
    def _normalize_write_vals(self, vals):
        """Normalize settings values before create/write."""
        normalized = dict(vals)
        if isinstance(normalized.get('fs_default_home_base'), str):
            normalized['fs_default_home_base'] = normalized['fs_default_home_base'].strip().upper()
        return normalized

    @api.model_create_multi
    def create(self, vals_list):
        """Normalize settings values before creation."""
        normalized_vals_list = [self._normalize_write_vals(vals) for vals in vals_list]
        return super().create(normalized_vals_list)

    def write(self, vals):
        """Normalize settings values before writing."""
        return super().write(self._normalize_write_vals(vals))

    @api.constrains('fs_default_home_base')
    def _check_default_home_base(self):
        """Validate the default home base ICAO code."""
        for record in self:
            if record.fs_default_home_base and not ICAO_CODE_PATTERN.fullmatch(record.fs_default_home_base):
                raise ValidationError(_('Default Home Base must be a 4-letter uppercase ICAO code.'))

    @api.onchange('fs_default_home_base')
    def _onchange_default_home_base(self):
        """Normalize the default home base in the settings form."""
        if self.fs_default_home_base:
            self.fs_default_home_base = self.fs_default_home_base.strip().upper()
