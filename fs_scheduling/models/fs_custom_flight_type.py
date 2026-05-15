# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs custom flight type module.

Purpose:
    Defines classes FsCustomFlightType for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import fields, models


class FsCustomFlightType(models.Model):
    """Non-syllabus flight activity types (e.g., test flight, conveying).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.custom.flight.type``.
        _description (str): Human-readable model label, ``Custom Flight Type``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """

    _name = 'fs.custom.flight.type'
    _description = 'Custom Flight Type'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
    )
    default_duration = fields.Float(
        string='Default Duration (Hours)',
        default=1.0,
    )
    is_exam = fields.Boolean(
        string='Is Exam',
        default=False,
        help="If enabled, this activity requires an instructor with examinator qualification.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
