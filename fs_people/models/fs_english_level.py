# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs english level module.

Purpose:
    Defines classes FsEnglishLevel for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from odoo import fields, models


class FsEnglishLevel(models.Model):
    """ICAO English proficiency levels (Level 4, 5, 6).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.english.level``.
        _description (str): Human-readable model label, ``English Proficiency Level``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

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
