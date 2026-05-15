# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs pilot function module.

Purpose:
    Defines classes FsPilotFunction for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import api, fields, models


class FsPilotFunction(models.Model):
    """Configurable pilot function/role for flights.

    This model defines the available pilot functions and their hour counting behavior.
    The 'code' field links to the existing Selection field values for compatibility.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.pilot.function``.
        _description (str): Human-readable model label, ``Pilot Function``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """

    _name = 'fs.pilot.function'
    _description = 'Pilot Function'
    _order = 'sequence, id'

    code = fields.Char(
        string='Code',
        required=True,
        help="Technical code matching the Selection field value.",
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    is_counted_flight = fields.Boolean(
        string='Count Flight Hours',
        default=True,
        help="If checked, hours with this function count toward total flight hours.",
    )
    is_counted_instructor = fields.Boolean(
        string='Count Instruction Hours',
        default=False,
        help="If checked, hours with this function count toward instruction hours.",
    )
    is_counted_solo = fields.Boolean(
        string='Count Solo Hours',
        default=False,
        help="If checked, hours with this function count toward solo hours.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Pilot function code must be unique!',
    )

    @api.model
    def get_function_by_code(self, code):
        """Get pilot function record by code.

        Args:
            code: Configured pilot-function code to search for.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        if not code:
            return False
        return self.search([('code', '=', code)], limit=1)
