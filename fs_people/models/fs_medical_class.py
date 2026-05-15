# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs medical class module.

Purpose:
    Defines classes FsMedicalClass for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models


class FsMedicalClass(models.Model):
    """Medical class types configuration (Class 1, Class 2, etc.).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.medical.class``.
        _description (str): Human-readable model label, ``Medical Class``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

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
