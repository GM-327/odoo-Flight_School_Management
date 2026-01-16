# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsFlightRoute(models.Model):
    """Specific working areas or flight routes used for scheduling."""
    _name = 'fs.flight.route'
    _description = 'Flight Route / Area'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
