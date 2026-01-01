# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsCustomFlightType(models.Model):
    """Non-syllabus flight activity types (e.g., test flight, conveying)."""

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
    active = fields.Boolean(
        string='Active',
        default=True,
    )
