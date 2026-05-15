# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs instructor availability module.

Purpose:
    Defines classes FsInstructorAvailability for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models


class FsInstructorAvailability(models.Model):
    """Instructor availability records for scheduling.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.instructor.availability``.
        _description (str): Human-readable model label, ``Instructor Availability``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

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
