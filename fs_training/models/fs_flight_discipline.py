# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs flight discipline module.

Purpose:
    Defines classes FsFlightDiscipline for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import fields, models


class FsFlightDiscipline(models.Model):
    """Flight discipline categories (MAN, NAV, IFR, VSV, etc.).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.discipline``.
        _description (str): Human-readable model label, ``Flight Discipline``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.flight.discipline'
    _description = 'Flight Discipline'
    _order = 'sequence, name'
    _rec_names_search = ['name', 'code']

    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.display_name = record.code or record.name

    name = fields.Char(
        string='Name',
        required=True,
        help="Full name of the discipline (e.g., Maneuvering, Navigation).",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code (e.g., MAN, NAV, IFR, VSV).",
    )
    default_flight_duration = fields.Float(
        string='Default Duration (Hours)',
        default=1.0,
        help="Default flight duration for missions of this discipline.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for badge display (0-11).",
    )
    description = fields.Text(
        string='Description',
        help="Description of this discipline.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Discipline code must be unique!',
    )
