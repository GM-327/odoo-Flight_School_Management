# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsPilotFunction(models.Model):
    """Configurable pilot function/role for flights.

    This model defines the available pilot functions and their hour counting behavior.
    The 'code' field links to the existing Selection field values for compatibility.
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

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Pilot function code must be unique!'),
    ]

    @api.model
    def get_function_by_code(self, code):
        """Get pilot function record by code.

        Args:
            code: Selection field value (e.g., 'instructor', 'student')

        Returns:
            fs.pilot.function record or False
        """
        if not code:
            return False
        return self.search([('code', '=', code)], limit=1)
