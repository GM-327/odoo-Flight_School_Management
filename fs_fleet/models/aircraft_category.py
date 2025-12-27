# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AircraftCategory(models.Model):
    """Aircraft category classification (single-engine, multi-engine, etc.)."""

    _name = 'fs.aircraft.category'
    _description = 'Aircraft Category'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help="Name of the aircraft category.",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code for the category (e.g., SEP, MEP).",
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help="Detailed description of this aircraft category.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order in lists and dropdowns.",
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for kanban views.",
    )
    aircraft_type_ids = fields.One2many(
        comodel_name='fs.aircraft.type',
        inverse_name='category_id',
        string='Aircraft Types',
        help="Types of aircraft in this category.",
    )
    aircraft_type_count = fields.Integer(
        string='Types Count',
        compute='_compute_aircraft_type_count',
        store=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this category.",
    )
    is_simulator = fields.Boolean(
        string='Is Simulator',
        default=False,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Category code must be unique!',
    )
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Category name must be unique!',
    )

    @api.depends('aircraft_type_ids')
    def _compute_aircraft_type_count(self):
        for record in self:
            record.aircraft_type_count = len(record.aircraft_type_ids)

    @api.constrains('code')
    def _check_code_uppercase(self):
        for record in self:
            if record.code and record.code != record.code.upper():
                raise UserError("Category code must be uppercase.")

    @api.onchange('code')
    def _onchange_code_uppercase(self):
        if self.code:
            self.code = self.code.upper()

    def unlink(self):
        for record in self:
            if record.aircraft_type_ids:
                raise UserError(
                    f"Cannot delete category '{record.name}' because it has "
                    f"{len(record.aircraft_type_ids)} aircraft type(s) assigned. "
                    "Archive it instead."
                )
        return super().unlink()
