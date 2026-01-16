# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school training module."""

    _name = 'res.config.settings'
    _inherit = ['res.config.settings']

    # === Training Warnings ===
    fs_training_class_end_warning_days = fields.Integer(
        string='Class End Warning (Days)',
        default=14,
        config_parameter='flight_school.class_end_warning_days',
        help="Days before training class expected end date to flag students.",
    )
