# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FsInstructorQualification(models.Model):
    """Instructor Qualification - Configurable set of qualifications."""

    _name = 'fs.instructor.qualification'
    _description = 'Instructor Qualification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    typical_validity_months = fields.Integer(
        string='Typical Validity (Months)',
        required=True,
        default=12,
        help='Number of months the qualification typically remains valid. '
             'Validity dates derived from this field should be rounded to the end of the month.'
    )

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Qualification name must be unique.'
    )

    @api.constrains('typical_validity_months')
    def _check_validity_months(self):
        for record in self:
            if record.typical_validity_months <= 0:
                raise ValidationError(_("Typical validity duration must be greater than zero."))


class FsInstructorQualificationAssignment(models.Model):
    """Link instructors to qualifications with expiry tracking."""

    _name = 'fs.instructor.qualification.assignment'
    _description = 'Instructor Qualification Assignment'
    _order = 'expiry_date, id'

    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        required=True,
        ondelete='cascade'
    )
    qualification_id = fields.Many2one(
        comodel_name='fs.instructor.qualification',
        string='Qualification',
        required=True,
        ondelete='restrict'
    )
    expiry_date = fields.Date(string='Expiry Date', required=True)
    status = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
            ('current', 'Current'),
            ('expiring_soon', 'Expiring Soon'),
            ('expired', 'Expired'),
        ],
        string='Status',
        compute='_compute_status',
        store=True
    )
    color = fields.Integer(string='Color', compute='_compute_color', store=True)

    @api.depends('qualification_id.code', 'qualification_id.name')
    def _compute_display_name(self):
        for record in self:
            # Use the qualification code for display if available, otherwise fallback to name
            q = record.qualification_id
            record.display_name = q.code or q.name or ""  # type: ignore

    @api.depends('status')
    def _compute_color(self):
        for record in self:
            if record.status == 'current':
                record.color = 10  # Green
            elif record.status == 'expiring_soon':
                record.color = 2   # Orange
            elif record.status == 'expired':
                record.color = 1   # Red
            else:
                record.color = 0   # Grey

    _qualification_unique_per_instructor = models.Constraint(
        'UNIQUE(instructor_id, qualification_id)',
        'Each qualification can only be assigned once per instructor.'
    )

    @api.depends('expiry_date')
    def _compute_status(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.expiry_date:
                record.status = 'unknown'
                continue
            if record.expiry_date < today:
                record.status = 'expired'
            elif record.expiry_date <= today + relativedelta(days=30):
                record.status = 'expiring_soon'
            else:
                record.status = 'current'
