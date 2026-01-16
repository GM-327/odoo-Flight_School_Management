# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school core module.
    
    This is the base settings class that provides general settings.
    Other flight school modules extend this with their own settings.
    """

    _name = 'res.config.settings'
    _inherit = ['res.config.settings']

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
