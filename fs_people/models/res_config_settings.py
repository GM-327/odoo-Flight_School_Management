# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People res config settings module.

Purpose:
    Defines classes ResConfigSettings for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models

from .fs_person import COMPLIANCE_WARNING_DEFAULTS


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school personnel module.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

    _inherit = 'res.config.settings'

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

    # === Personnel Warning Periods ===
    fs_medical_warning_days = fields.Integer(
        string='Medical Expiry Warning (Days)',
        default=COMPLIANCE_WARNING_DEFAULTS['medical_warning_days'],
        config_parameter='flight_school.medical_warning_days',
        help="Days before medical certificate expiry to show warnings.",
    )
    fs_license_warning_days = fields.Integer(
        string='License/Qualification Expiry Warning (Days)',
        default=COMPLIANCE_WARNING_DEFAULTS['license_warning_days'],
        config_parameter='flight_school.license_warning_days',
        help="Days before license or qualification expiry to show warnings.",
    )
    fs_english_warning_days = fields.Integer(
        string='English Proficiency Expiry Warning (Days)',
        default=COMPLIANCE_WARNING_DEFAULTS['english_warning_days'],
        config_parameter='flight_school.english_warning_days',
        help="Days before English proficiency expiry to show warnings.",
    )
    fs_insurance_warning_days = fields.Integer(
        string='Insurance Expiry Warning (Days)',
        default=COMPLIANCE_WARNING_DEFAULTS['insurance_warning_days'],
        config_parameter='flight_school.insurance_warning_days',
        help="Days before insurance expiry to show warnings (civilians).",
    )
    fs_security_warning_days = fields.Integer(
        string='Security Clearance Expiry Warning (Days)',
        default=COMPLIANCE_WARNING_DEFAULTS['security_warning_days'],
        config_parameter='flight_school.security_warning_days',
        help="Days before security clearance expiry to show warnings (civilians).",
    )

    def _compliance_warning_values_changed(self):
        """Detect warning-window changes before settings are persisted."""
        parameter_store = self.env['ir.config_parameter'].sudo()
        for field_name, setting_name in (
            ('fs_medical_warning_days', 'medical_warning_days'),
            ('fs_license_warning_days', 'license_warning_days'),
            ('fs_english_warning_days', 'english_warning_days'),
            ('fs_security_warning_days', 'security_warning_days'),
            ('fs_insurance_warning_days', 'insurance_warning_days'),
        ):
            stored_value = parameter_store.get_param(
                f'flight_school.{setting_name}',
                str(COMPLIANCE_WARNING_DEFAULTS[setting_name]),
            )
            try:
                stored_value = int(stored_value)
            except (TypeError, ValueError):
                stored_value = COMPLIANCE_WARNING_DEFAULTS[setting_name]
            if stored_value != getattr(self, field_name):
                return True
        return False

    def set_values(self):
        """Persist settings and immediately refresh affected stored statuses."""
        warning_values_changed = self._compliance_warning_values_changed()
        result = super().set_values()
        if warning_values_changed:
            self.env['fs.person']._recompute_compliance_statuses(full=True)
        return result
