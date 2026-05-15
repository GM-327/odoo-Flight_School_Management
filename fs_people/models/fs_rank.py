# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs rank module.

Purpose:
    Defines classes FsRank for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models


class FsRank(models.Model):
    """Military ranks for personnel.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.rank``.
        _description (str): Human-readable model label, ``Military Rank``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

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
