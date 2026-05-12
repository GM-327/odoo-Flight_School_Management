# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school fleet module."""

    _inherit = 'res.config.settings'

    # === Aircraft Maintenance Warnings ===
    fs_maintenance_warning_days = fields.Integer(
        string='Maintenance Date Warning (Days)',
        default=7,
        config_parameter='flight_school.maintenance_warning_days',
        help="Days before aircraft maintenance due date to show warnings.",
    )
    fs_maintenance_warning_hours = fields.Float(
        string='Maintenance Warning (Hours)',
        default=5.0,
        config_parameter='flight_school.maintenance_warning_hours',
        help="Hours before maintenance is due to show warnings.",
    )
