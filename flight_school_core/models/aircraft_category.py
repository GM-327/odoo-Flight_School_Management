# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsAircraftCategory(models.Model):
    """Aircraft Category - configurable grouping for aircraft types."""

    _name = 'fs.aircraft.category'
    _description = 'Aircraft Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Aircraft category name must be unique.'
    )
