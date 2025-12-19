# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration entries for flight school defaults."""

    _name = 'res.config.settings'
    _inherit = ['res.config.settings']

    fs_default_home_base = fields.Char(
        string='Default Home Base',
        default='DTTI',
        config_parameter='flight_school.default_home_base',
        help="ICAO airport code used as the default home base for new aircraft.",
    )
    fs_default_max_students = fields.Integer(
        string='Default Max Students per Instructor',
        default=8,
        config_parameter='flight_school.default_max_students',
        help="Number of students assigned by default when creating new instructors.",
    )
    fs_default_max_hours_per_month = fields.Float(
        string='Default Max Hours / Month',
        default=80.0,
        config_parameter='flight_school.default_max_hours_per_month',
        help="Monthly instruction-hour limit suggested for new instructors.",
    )
    fs_default_max_hours_per_3months = fields.Float(
        string='Default Max Hours / 3 Months',
        default=240.0,
        config_parameter='flight_school.default_max_hours_per_3months',
        help="Rolling 3-month instruction-hour limit suggested for new instructors.",
    )
    fs_medical_warning_days = fields.Integer(
        string='Medical Expiry Warning Period (Days)',
        default=30,
        config_parameter='flight_school.medical_warning_days',
        help="Number of days before medical certificate expiry to start showing warnings.",
    )
    fs_training_class_end_warning_days = fields.Integer(
        string='Class End Warning Period (Days)',
        default=14,
        config_parameter='flight_school.class_end_warning_days',
        help="Days before a training class expected end date to flag students as nearing completion.",
    )
