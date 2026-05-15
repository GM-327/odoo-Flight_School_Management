# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training res config settings module.

Purpose:
    Defines classes ResConfigSettings for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school training module.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _inherit = 'res.config.settings'

    # === Training Warnings ===
    fs_training_class_end_warning_days = fields.Integer(
        string='Class End Warning (Days)',
        default=14,
        config_parameter='flight_school.class_end_warning_days',
        help="Days before training class expected end date to flag students.",
    )
