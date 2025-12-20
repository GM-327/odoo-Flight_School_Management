# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsQualificationType(models.Model):
    """Qualification types configuration (IR, ME, FI, SEP, MEP)."""
    
    _name = 'fs.qualification.type'
    _description = 'Qualification Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Qualification Name',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        help="Short code (e.g., IR, ME, FI).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        help="Validity period in months.",
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Qualification code must be unique!',
    )
