# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs flight type module.

Purpose:
    Defines classes FsFlightType for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import fields, models


class FsFlightType(models.Model):
    """Flight types (Solo, Dual).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.type``.
        _description (str): Human-readable model label, ``Flight Type``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.flight.type'
    _description = 'Flight Type'
    _order = 'sequence, name'
    _rec_names_search = ['name', 'code']

    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.display_name = record.code or record.name

    name = fields.Char(
        string='Name',
        required=True,
        help="Flight type name (e.g., Solo, Dual).",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code (e.g., SOLO, DUAL).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for badge display (0-11).",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    is_solo = fields.Boolean(
        string='Is Solo',
        default=False,
        help="Mark if this flight type is a solo flight.",
    )
    is_sim = fields.Boolean(
        string='Is Simulator',
        default=False,
        help="Mark if this flight type is a simulator session.",
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Flight type code must be unique!',
    )
