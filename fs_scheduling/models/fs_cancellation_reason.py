# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs cancellation reason module.

Purpose:
    Defines classes FsCancellationReason for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import api, fields, models


class FsCancellationReason(models.Model):
    """Configurable reasons for flight mission cancellation.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.cancellation.reason``.
        _description (str): Human-readable model label, ``Cancellation Reason``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """

    _name = 'fs.cancellation.reason'
    _description = 'Cancellation Reason'
    _order = 'code'

    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help="Short code for display (e.g., WX, MAINT, SICK)",
    )
    name = fields.Char(
        string='Reason',
        required=True,
    )
    color = fields.Integer(
        string='Color',
        default=1,  # Red
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Cancellation reason code must be unique!',
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.display_name = f"[{record.code}] {record.name}" if record.code else record.name
