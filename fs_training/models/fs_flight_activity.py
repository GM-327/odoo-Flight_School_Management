# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsFlightActivity(models.Model):
    """Pair of Flight Discipline and Flight Type (e.g., MAN-SOLO, NAV-DUAL)."""

    _name = 'fs.flight.activity'
    _description = 'Flight Activity'
    _order = 'discipline_id, flight_type_id'
    _rec_names_search = ['name', 'code']

    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        string='Discipline',
        required=True,
        ondelete='restrict',
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        string='Flight Type',
        required=True,
        ondelete='restrict',
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name_and_code',
        store=True,
    )
    code = fields.Char(
        string='Code',
        compute='_compute_name_and_code',
        store=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _unique_activity = models.Constraint(
        'UNIQUE(discipline_id, flight_type_id)',
        'This combination of Discipline and Flight Type already exists!',
    )

    @api.depends('discipline_id.name', 'discipline_id.code', 
                 'flight_type_id.name', 'flight_type_id.code')
    def _compute_name_and_code(self):
        for record in self:
            discipline_name = record.discipline_id['name'] or ''
            flight_type_name = record.flight_type_id['name'] or ''
            discipline_code = record.discipline_id['code'] or ''
            flight_type_code = record.flight_type_id['code'] or ''
            
            record.name = f"{discipline_name} ({flight_type_name})"
            record.code = f"{discipline_code}-{flight_type_code}"

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.code or record.name
