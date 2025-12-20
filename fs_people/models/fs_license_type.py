# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsLicenseType(models.Model):
    """License types configuration (PPL, CPL, ATPL, Student Card)."""
    
    _name = 'fs.license.type'
    _description = 'License Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='License Name',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        help="Short code (e.g., PPL, CPL).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    has_validity = fields.Boolean(
        string='Has Validity Period',
        default=False,
        help="Only Student Card typically has a validity period.",
    )
    is_student_related = fields.Boolean(
        string='Is Student Related',
        default=False,
        help="Only Student Card is student related.",
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        help="Validity period in months (if applicable).",
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
        'License code must be unique!',
    )
