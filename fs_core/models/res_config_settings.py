# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school modules."""

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

    # === Instructor Limits ===
    fs_default_max_students = fields.Integer(
        string='Default Max Students per Instructor',
        default=6,
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

    # === Warning Periods ===
    fs_medical_warning_days = fields.Integer(
        string='Medical Expiry Warning (Days)',
        default=35,
        config_parameter='flight_school.medical_warning_days',
        help="Days before medical certificate expiry to show warnings.",
    )
    fs_license_warning_days = fields.Integer(
        string='License/Qualification Expiry Warning (Days)',
        default=35,
        config_parameter='flight_school.license_warning_days',
        help="Days before license or qualification expiry to show warnings.",
    )
    fs_english_warning_days = fields.Integer(
        string='English Proficiency Expiry Warning (Days)',
        default=60,
        config_parameter='flight_school.english_warning_days',
        help="Days before English proficiency expiry to show warnings.",
    )
    fs_insurance_warning_days = fields.Integer(
        string='Insurance Expiry Warning (Days)',
        default=14,
        config_parameter='flight_school.insurance_warning_days',
        help="Days before insurance expiry to show warnings (civilians).",
    )
    fs_security_warning_days = fields.Integer(
        string='Security Clearance Expiry Warning (Days)',
        default=60,
        config_parameter='flight_school.security_warning_days',
        help="Days before security clearance expiry to show warnings (civilians).",
    )
    fs_training_class_end_warning_days = fields.Integer(
        string='Class End Warning (Days)',
        default=14,
        config_parameter='flight_school.class_end_warning_days',
        help="Days before training class expected end date to flag students.",
    )
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
