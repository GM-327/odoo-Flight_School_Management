# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs class requirement module.

Purpose:
    Defines classes FsClassRequirement for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import fields, models


class FsClassRequirement(models.Model):
    """Enrollment requirements for training classes.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.class.requirement``.
        _description (str): Human-readable model label, ``Class Requirement``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.class.requirement'
    _description = 'Class Requirement'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help="Requirement name (e.g., Valid Medical, PPL License).",
    )
    category = fields.Selection(
        selection=[
            ('medical', 'Medical'),
            ('license', 'License'),
            ('qualification', 'Qualification'),
            ('english', 'English Proficiency'),
            ('security_clearance', 'Security Clearance'),
            ('insurance', 'Insurance'),
            ('other', 'Other / Manual Check'),
        ],
        string='Category',
        default='other',
        help="Link to expiry-tracked field for automatic validation.",
    )
    is_military = fields.Boolean(
        string='Military',
        default=True,
        help="Applies to military students.",
    )
    is_civilian = fields.Boolean(
        string='Civilian',
        default=True,
        help="Applies to civilian students.",
    )
    is_default = fields.Boolean(
        string='Default',
        default=False,
        help="Automatically add to new class types.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
