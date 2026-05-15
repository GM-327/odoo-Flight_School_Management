# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs qualification type module.

Purpose:
    Defines classes FsQualificationType for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models


class FsQualificationType(models.Model):
    """Qualification types configuration (IR, ME, FI, SEP, MEP).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.qualification.type``.
        _description (str): Human-readable model label, ``Qualification Type``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

    _name = 'fs.qualification.type'
    _description = 'Qualification Type'
    _order = 'sequence, name'
    _rec_name = 'code'

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
    is_examinator = fields.Boolean(
        string='Examinator Qualification',
        default=False,
        help="If checked, instructors with this qualification can conduct exam missions.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Qualification code must be unique!',
    )
