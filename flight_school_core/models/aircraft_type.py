# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _


class FsAircraftType(models.Model):
    """Aircraft Type - catalog of training aircraft types."""

    _name = 'fs.aircraft.type'
    _description = 'Aircraft Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Name', required=True, tracking=True, help="Type name, e.g., Cessna 172.")
    manufacturer = fields.Char(string='Manufacturer', tracking=True)
    model_name = fields.Char(string='Model', tracking=True)
    category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Category',
        tracking=True,
        help="Category for this aircraft type."
    )
    active = fields.Boolean(string='Active', default=True, tracking=True)

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Aircraft type name must be unique.'
    )

    def _compute_display_name(self):
        for record in self:
            parts = [record.name, record.model_name, record.manufacturer]
            record.display_name = " - ".join([str(p) for p in parts if p])

    # === CRUD Overrides ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
            if vals.get('manufacturer'):
                vals['manufacturer'] = vals['manufacturer'].upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        if vals.get('manufacturer'):
            vals['manufacturer'] = vals['manufacturer'].upper()
        return super().write(vals)

    # === Onchange Helpers ===
    @api.onchange('name', 'manufacturer')
    def _onchange_uppercase_fields(self):
        if self.name:
            self.name = self.name.upper()
        if self.manufacturer:
            self.manufacturer = self.manufacturer.upper()
