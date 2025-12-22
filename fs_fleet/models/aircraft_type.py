# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AircraftType(models.Model):
    """Aircraft type/model definition (e.g., Cessna 172, Diamond DA40)."""

    _name = 'fs.aircraft.type'
    _description = 'Aircraft Type'
    _order = 'manufacturer, name'

    name = fields.Char(
        string='Model Name',
        required=True,
        help="Aircraft model name (e.g., 172S Skyhawk, DA40 Diamond Star).",
    )
    manufacturer = fields.Char(
        string='Manufacturer',
        required=True,
        help="Aircraft manufacturer (e.g., Cessna, Diamond, Piper).",
    )
    full_name = fields.Char(
        string='Full Name',
        compute='_compute_full_name',
        store=True,
        help="Full name combining manufacturer and model.",
    )
    category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Category',
        required=True,
        ondelete='restrict',
        help="Aircraft category (single-engine, multi-engine, etc.).",
    )
    code = fields.Char(
        string='ICAO Type Code',
        help="ICAO aircraft type designator (e.g., C172, DA40, P28A).",
    )
    description = fields.Text(
        string='Description',
        help="Detailed description of this aircraft type.",
    )
    
    # Technical specifications
    engine_count = fields.Integer(
        string='Number of Engines',
        default=1,
    )
    engine_type = fields.Selection(
        selection=[
            ('piston', 'Piston'),
            ('turboprop', 'Turboprop'),
            ('jet', 'Jet'),
            ('electric', 'Electric'),
        ],
        string='Engine Type',
        default='piston',
    )
    is_complex = fields.Boolean(
        string='Complex Aircraft',
        default=False,
        help="Has retractable gear, flaps, and controllable propeller.",
    )
    is_high_performance = fields.Boolean(
        string='High Performance',
        default=False,
        help="Engine with more than 200 horsepower.",
    )
    seats = fields.Integer(
        string='Seats',
        default=4,
        help="Number of seats including pilot.",
    )
    
    # Training suitability
    suitable_for_training = fields.Boolean(
        string='Suitable for Training',
        default=True,
    )
    training_notes = fields.Text(
        string='Training Notes',
        help="Notes about using this type for training.",
    )
    
    # Related aircraft
    aircraft_ids = fields.One2many(
        comodel_name='fs.aircraft',
        inverse_name='aircraft_type_id',
        string='Aircraft',
    )
    aircraft_count = fields.Integer(
        string='Fleet Count',
        compute='_compute_aircraft_count',
        store=True,
    )
    
    # Image
    image = fields.Image(
        string='Image',
        max_width=1024,
        max_height=1024,
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _manufacturer_name_unique = models.Constraint(
        'UNIQUE(manufacturer, name)',
        'This aircraft type already exists for this manufacturer!',
    )

    @api.depends('manufacturer', 'name')
    def _compute_full_name(self):
        for record in self:
            if record.manufacturer and record.name:
                record.full_name = f"{record.manufacturer} {record.name}"
            else:
                record.full_name = record.name or ''

    @api.depends('aircraft_ids')
    def _compute_aircraft_count(self):
        for record in self:
            record.aircraft_count = len(record.aircraft_ids)

    def name_get(self):
        """Display full name (manufacturer + model) in dropdowns."""
        return [(rec.id, rec.full_name or rec.name) for rec in self]

    def unlink(self):
        for record in self:
            if record.aircraft_ids:
                raise UserError(
                    f"Cannot delete type '{record.full_name}' because it has "
                    f"{len(record.aircraft_ids)} aircraft assigned. "
                    "Archive it instead."
                )
        return super().unlink()
