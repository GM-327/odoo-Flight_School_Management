# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsFlightDiscipline(models.Model):
    """Flight discipline categories (MAN, NAV, IFR, VSV, etc.)."""

    _name = 'fs.flight.discipline'
    _description = 'Flight Discipline'
    _order = 'sequence, name'
    _rec_names_search = ['name', 'code']

    def _compute_display_name(self):
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
