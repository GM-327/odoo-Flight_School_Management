# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsFlightType(models.Model):
    """Flight types (Solo, Dual)."""

    _name = 'fs.flight.type'
    _description = 'Flight Type'
    _order = 'sequence, name'
    _rec_names_search = ['name', 'code']

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.code or record.name

    name = fields.Char(
        string='Name',
        required=True,
        help="Flight type name (e.g., Solo, Dual).",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code (e.g., SOLO, DUAL).",
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
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    is_solo = fields.Boolean(
        string='Is Solo',
        default=False,
        help="Mark if this flight type is a solo flight.",
    )
    is_sim = fields.Boolean(
        string='Is Simulator',
        default=False,
        help="Mark if this flight type is a simulator session.",
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Flight type code must be unique!',
    )
