# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs person qualification module.

Purpose:
    Defines classes FsPersonQualification for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FsPersonQualification(models.Model):
    """Person's qualification with issue/expiry tracking.

    This model links a person (instructor/pilot) to their qualifications
    with individual issue and expiry dates.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.person.qualification``.
        _description (str): Human-readable model label, ``Person Qualification``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

    _name = 'fs.person.qualification'
    _description = 'Person Qualification'
    _order = 'expiry_date'
    _rec_name = 'qualification_id'

    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        ondelete='cascade',
    )
    pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Pilot',
        ondelete='cascade',
    )
    qualification_id = fields.Many2one(
        comodel_name='fs.qualification.type',
        string='Qualification',
        required=True,
        ondelete='restrict',
    )
    qualification_code = fields.Char(
        string='Code',
        related='qualification_id.code',
    )
    qualification_name = fields.Char(
        string='Name',
        related='qualification_id.name',
    )
    issue_date = fields.Date(
        string='Issue Date',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        related='qualification_id.validity_months',
    )
    expiry_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Status',
        compute='_compute_expiry_status',
        store=True,
    )
    notes = fields.Text(
        string='Notes',
    )
    origin_qualification_id = fields.Many2one(
        comodel_name='fs.person.qualification',
        string='Origin Qualification',
        readonly=True,
        ondelete='set null',
        help='Source qualification copied during a role transition.',
    )
    transition_id = fields.Many2one(
        comodel_name='fs.person.role.transition',
        string='Role Transition',
        readonly=True,
        ondelete='set null',
        help='Transition that created this copied qualification.',
    )

    @api.constrains('instructor_id', 'pilot_id', 'qualification_id')
    def _check_single_owner(self):
        """Require each qualification to belong to exactly one person.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        for record in self:
            owner_count = int(bool(record.instructor_id)) + int(bool(record.pilot_id))
            if owner_count != 1:
                raise ValidationError(
                    self.env._("A qualification must be linked to exactly one instructor or one pilot.")
                )

    @api.depends('expiry_date')
    def _compute_expiry_status(self):
        """Compute expiry status based on expiry date and warning period from settings.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.license_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)

        for record in self:
            if not record.expiry_date:
                record.expiry_status = 'no_expiry'
            elif record.expiry_date < today:
                record.expiry_status = 'expired'
            elif record.expiry_date <= warning_date:
                record.expiry_status = 'expiring'
            else:
                record.expiry_status = 'valid'

    @api.onchange('qualification_id', 'issue_date')
    def _onchange_calculate_expiry(self):
        """Calculate expiry date based on issue date and validity months.

        The expiry date is set to the last day of the month after adding
        the validity period.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            validity_months = record.qualification_id.validity_months
            if record.issue_date and record.qualification_id and validity_months:  # type: ignore
                total_months = record.issue_date.month - 1 + validity_months
                expiry_year = record.issue_date.year + (total_months // 12)
                expiry_month = (total_months % 12) + 1
                if expiry_month == 12:
                    first_day_next_month = date(expiry_year + 1, 1, 1)
                else:
                    first_day_next_month = date(expiry_year, expiry_month + 1, 1)
                record.expiry_date = first_day_next_month - timedelta(days=1)
            else:
                record.expiry_date = False
