# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Fleet res config settings module.

Purpose:
    Defines classes ResConfigSettings for aircraft categories, aircraft types, aircraft records, maintenance awareness, and fleet dashboard data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school fleet module.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        fs_training defines aircraft-type requirements.
        fs_scheduling and fs_flights use aircraft availability and total-hour data.
    """

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
