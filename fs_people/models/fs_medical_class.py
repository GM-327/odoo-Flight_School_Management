# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsMedicalClass(models.Model):
    """Medical class types configuration (Class 1, Class 2, etc.)."""
    
    _name = 'fs.medical.class'
    _description = 'Medical Class'
    _order = 'sequence, name'

    name = fields.Char(
        string='Medical Class Name',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        help="Short code (e.g., C1, C2).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        help="Default validity period in months.",
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
        'Medical class code must be unique!',
    )
