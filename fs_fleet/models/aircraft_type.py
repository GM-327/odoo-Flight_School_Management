# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Fleet aircraft type module.

Purpose:
    Defines classes AircraftType for aircraft categories, aircraft types, aircraft records, maintenance awareness, and fleet dashboard data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AircraftType(models.Model):
    """Aircraft type/model definition (e.g., Cessna 172, Diamond DA40).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.aircraft.type``.
        _description (str): Human-readable model label, ``Aircraft Type``.

    Related:
        fs_training defines aircraft-type requirements.
        fs_scheduling and fs_flights use aircraft availability and total-hour data.
    """

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

    # Pricing
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,  # type: ignore
    )
    hour_price_solo = fields.Monetary(
        string='Solo Hour Price',
        currency_field='currency_id',
        help="Hourly rate for solo flights.",
    )
    hour_price_dual = fields.Monetary(
        string='Dual Hour Price',
        currency_field='currency_id',
        help="Hourly rate for dual (instructor) flights.",
    )
    hour_price_sim = fields.Monetary(
        string='Simulator Hour Price',
        currency_field='currency_id',
        help="Hourly rate for simulator sessions.",
    )
    is_simulator = fields.Boolean(
        string='Is Simulator',
        related='category_id.is_simulator',
        store=True,
        readonly=True,
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
        """Compute full name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.manufacturer and record.name:
                record.full_name = f"{record.manufacturer} {record.name}"
            else:
                record.full_name = record.name or ''

    @api.depends('full_name', 'name')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.display_name = record.full_name or record.name or _('New Aircraft Type')

    @api.depends('aircraft_ids')
    def _compute_aircraft_count(self):
        """Compute aircraft count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.aircraft_count = len(record.aircraft_ids)

    def unlink(self):
        """Delete records after enforcing Flight School business safeguards.

        Returns:
            bool: True when Odoo successfully deletes the records.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.aircraft_ids:
                raise UserError(
                    _(
                        "Cannot delete type '%(name)s' because it has %(count)s aircraft assigned. "
                        "Archive it instead.",
                        name=record.full_name,
                        count=len(record.aircraft_ids),
                    )
                )
        return super().unlink()
