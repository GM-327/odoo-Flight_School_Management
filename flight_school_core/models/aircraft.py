# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import re

from psycopg2 import sql

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.sql import column_exists


class FsAircraft(models.Model):
    """Aircraft - Basic fleet record."""

    _name = 'fs.aircraft'
    _description = 'Training Aircraft'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'registration'

    registration = fields.Char(
        string='Registration',
        required=True,
        tracking=True,
        default='TS-',
        size=6,
        help="Enter registration in TS-XXX format."
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Aircraft Type',
        required=True,
        tracking=True,
        help="Select the configured aircraft type."
    )
    manufacturer = fields.Char(string='Manufacturer', related='aircraft_type_id.manufacturer', store=True, readonly=True)
    model_name = fields.Char(string='Model', related='aircraft_type_id.model_name', store=True, readonly=True)
    category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Category',
        related='aircraft_type_id.category_id',
        store=True,
        readonly=True
    )
    serial_number = fields.Char(string='Serial Number')
    year_manufactured = fields.Char(
        string='Year Manufactured',
        size=4,
        help="Enter the 4-digit manufacturing year (YYYY)."
    )
    total_hours = fields.Float(string='Total Hours')
    photo = fields.Binary(string='Photo', attachment=True)
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('maintenance', 'Maintenance'),
            ('grounded', 'Grounded'),
            ('reserved', 'Reserved'),
        ],
        string='Status',
        default='available',
        tracking=True
    )
    home_base = fields.Char(
        default=lambda self: self._get_default_home_base(),
        string='Home Base',
        size=4,
        help="Enter ICAO airport code (4 letters, e.g., DTTI)."
    )
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True, tracking=True)

    _registration_unique = models.Constraint(
        'UNIQUE(registration)',
        'Aircraft registration must be unique.'
    )
    _year_manufactured_format = models.Constraint(
        "CHECK(year_manufactured IS NULL OR (char_length(year_manufactured)=4 AND year_manufactured ~ '^[0-9]+$'))",
        'Year manufactured must be a 4-digit numeric value.'
    )

    def unlink(self):
        """Archive instead of deleting to preserve history."""
        self.write({'active': False})
        return True

    # === CRUD Overrides ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('registration'):
                vals['registration'] = self._normalize_registration(vals['registration'])
            if vals.get('home_base'):
                vals['home_base'] = vals['home_base'].upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('registration'):
            vals['registration'] = self._normalize_registration(vals['registration'])
        if vals.get('home_base'):
            vals['home_base'] = vals['home_base'].upper()
        return super().write(vals)

    # === Helpers ===
    @api.model
    def _get_default_home_base(self):
        # get_param is a method of ir.config_parameter, but the linter sees BaseModel
        value = self.env['ir.config_parameter'].sudo().get_param('flight_school.default_home_base', default='DTTI') or 'DTTI'  # type: ignore
        return str(value).upper()

    def _normalize_registration(self, value):
        """Ensure registration is uppercase and follows TS-XXX."""
        value = (value or '').upper().strip()
        if not value:
            return value
        if not value.startswith('TS-'):
            stripped = value.replace('TS', '', 1) if value.startswith('TS') else value
            stripped = stripped.lstrip('-')
            value = f"TS-{stripped}"
        prefix, _, suffix = value.partition('-')
        suffix = re.sub(r'[^A-Z]', '', suffix)
        suffix = suffix[:3]
        value = f"TS-{suffix}"
        return value

    # === Constraints ===
    @api.constrains('registration')
    def _check_registration_format(self):
        pattern = re.compile(r'^TS-[A-Z]{3}$')
        for record in self:
            if record.registration and not pattern.match(record.registration):
                raise ValidationError(_("Registration must follow TS-XXX format with letters only."))

    @api.constrains('home_base')
    def _check_home_base_format(self):
        pattern = re.compile(r'^[A-Z]{4}$')
        for record in self:
            if record.home_base and not pattern.match(record.home_base):
                raise ValidationError(_("Home base must be a 4-letter ICAO code (e.g., DTTJ)."))

    @api.constrains('year_manufactured')
    def _check_year_format(self):
        for record in self:
            if record.year_manufactured:
                year_str = record.year_manufactured.strip()
                if not year_str.isdigit() or len(year_str) != 4:
                    raise ValidationError(_("Year manufactured must be a 4-digit numeric value."))
                year = int(year_str)
                if year < 1900 or year > 2100:
                    raise ValidationError(_("Year manufactured must be between 1900 and 2100."))

    # === Onchange ===
    @api.onchange('registration')
    def _onchange_registration(self):
        if self.registration:
            self.registration = self._normalize_registration(self.registration)

    @api.onchange('home_base')
    def _onchange_home_base(self):
        if self.home_base:
            self.home_base = self.home_base.upper()

    @api.onchange('year_manufactured')
    def _onchange_year_manufactured(self):
        if self.year_manufactured:
            digits_only = ''.join(ch for ch in str(self.year_manufactured) if ch.isdigit())
            digits_only = digits_only[:4]
            self.year_manufactured = digits_only
            if digits_only and len(digits_only) == 4:
                year = int(digits_only)
                if year < 1900 or year > 2100:
                    return {
                        'warning': {
                            'title': _('Invalid Year'),
                            'message': _('Year must be a 4-digit number between 1900 and 2100.'),
                        }
                    }
        return {}

    # === Model Init Helpers ===
    @api.model
    def _auto_init(self):
        """Convert legacy date year column back to integer before schema update."""
        cr = self.env.cr
        table = self._table
        if column_exists(cr, table, 'year_manufactured'):
            cr.execute("""
                SELECT data_type
                  FROM information_schema.columns
                 WHERE table_name=%s AND column_name=%s
            """, (table, 'year_manufactured'))
            result = cr.fetchone()
            if result and result[0] in ('date', 'timestamp without time zone', 'timestamp with time zone', 'integer', 'bigint'):
                if result[0] in ('integer', 'bigint'):
                    conversion = "CASE WHEN year_manufactured IS NULL THEN NULL ELSE lpad(year_manufactured::text, 4, '0') END"
                else:
                    conversion = "CASE WHEN year_manufactured IS NULL THEN NULL ELSE to_char(year_manufactured, 'YYYY') END"
                cr.execute(sql.SQL("""
                    ALTER TABLE {table}
                    ALTER COLUMN year_manufactured TYPE varchar(4)
                    USING {conversion}
                """).format(
                    table=sql.Identifier(table),
                    conversion=sql.SQL(conversion)
                ))
        return super()._auto_init()
