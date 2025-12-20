# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsRank(models.Model):
    """Military ranks for personnel."""
    
    _name = 'fs.rank'
    _description = 'Military Rank'
    _order = 'sequence, name'

    name = fields.Char(
        string='Rank Name',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        help="Short code for the rank (e.g., CPT for Captain).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used to order ranks from lowest to highest.",
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Rank name must be unique!',
    )
    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Rank code must be unique!',
    )
