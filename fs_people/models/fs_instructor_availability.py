# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsInstructorAvailability(models.Model):
    """Instructor availability records for scheduling."""

    _name = 'fs.instructor.availability'
    _description = 'Instructor Availability'
    _order = 'date desc, instructor_id'

    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )
    is_available = fields.Boolean(
        string='Is Available',
        default=True,
    )
    reason = fields.Char(
        string='Reason',
        help="Reason for unavailability (e.g., Leave, Meeting, Sick).",
    )

    _unique_instructor_date = models.Constraint(
        'UNIQUE(instructor_id, date)',
        'Availability record already exists for this instructor on this date!',
    )
