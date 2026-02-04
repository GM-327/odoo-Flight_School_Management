# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsCancellationReason(models.Model):
    """Configurable reasons for flight mission cancellation."""

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

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}" if record.code else record.name
