# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsEnglishLevel(models.Model):
    """ICAO English proficiency levels (Level 4, 5, 6)."""
    
    _name = 'fs.english.level'
    _description = 'English Proficiency Level'
    _order = 'level'

    name = fields.Char(
        string='Level Name',
        required=True,
        translate=True,
    )
    level = fields.Integer(
        string='Level',
        required=True,
        help="ICAO level (4, 5, or 6).",
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        help="Validity period in months. Level 6 is usually permanent.",
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _level_unique = models.Constraint(
        'UNIQUE(level)',
        'English level must be unique!',
    )
