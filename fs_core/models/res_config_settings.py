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
from odoo import fields, models


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
