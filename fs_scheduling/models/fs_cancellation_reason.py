# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsCancellationReason(models.Model):
    """Configurable reasons for flight mission cancellation."""

    _name = 'fs.cancellation.reason'
    _description = 'Cancellation Reason'
    _order = 'name'

    name = fields.Char(
        string='Reason',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
