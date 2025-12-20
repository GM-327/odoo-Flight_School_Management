# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date


class Aircraft(models.Model):
    """Individual aircraft in the training fleet."""

    _name = 'fs.aircraft'
    _description = 'Aircraft'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'registration'

    # === Basic Information ===
    registration = fields.Char(
        string='Registration',
        required=True,
        tracking=True,
        help="Aircraft registration number (e.g., TS-APR, N12345).",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Aircraft Type',
        required=True,
        tracking=True,
        ondelete='restrict',
        help="Make and model of the aircraft.",
    )
    category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Category',
        related='aircraft_type_id.category_id',
        store=True,
        readonly=True,
    )
    manufacturer = fields.Char(
        string='Manufacturer',
        related='aircraft_type_id.manufacturer',
        store=True,
        readonly=True,
    )
    
    # === Identification ===
    serial_number = fields.Char(
        string='Serial Number',
        help="Manufacturer's serial number.",
    )
    year_manufactured = fields.Integer(
        string='Year Manufactured',
    )
    
    # === Status ===
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'In Maintenance'),
            ('grounded', 'Grounded'),
            ('reserved', 'Reserved'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
        help="Current operational status of the aircraft.",
    )
    status_reason = fields.Text(
        string='Status Reason',
        tracking=True,
        help="Reason for current status (especially for grounded/maintenance).",
    )
    status_color = fields.Integer(
        string='Status Color',
        compute='_compute_status_color',
    )
    is_airworthy = fields.Boolean(
        string='Airworthy',
        compute='_compute_is_airworthy',
        store=True,
        help="Aircraft is available or in use (can fly).",
    )
    
    # === Hours Tracking ===
    total_hours = fields.Float(
        string='Total Hours',
        default=0.0,
        tracking=True,
        help="Total flight hours (airframe/Hobbs time).",
    )
    # tach_time = fields.Float(
    #     string='Tach Time',
    #     default=0.0,
    #     help="Current tachometer reading.",
    # )
    hours_since_overhaul = fields.Float(
        string='Hours Since Overhaul',
        default=0.0,
        help="Engine hours since last major overhaul.",
    )
    
    # === Maintenance ===
    last_maintenance_date = fields.Date(
        string='Last Maintenance',
        tracking=True,
    )
    next_maintenance_date = fields.Date(
        string='Next Maintenance Due Date',
        tracking=True,
    )
    maintenance_due_at_hours = fields.Float(
        string='Maintenance Due At (Hours)',
        help="Total airframe hours when next maintenance is due.",
    )
    remaining_maintenance_hours = fields.Float(
        string='Hours Remaining',
        compute='_compute_remaining_maintenance_hours',
        store=True,
        help="Remaining hours until next maintenance.",
    )
    maintenance_status = fields.Selection(
        selection=[
            ('ok', 'OK'),
            ('due_soon', 'Due Soon'),
            ('overdue', 'Overdue'),
        ],
        string='Maintenance Status',
        compute='_compute_maintenance_status',
        store=True,
    )
    annual_inspection_date = fields.Date(
        string='Annual Inspection Due',
        tracking=True,
    )
    annual_inspection_due_soon = fields.Boolean(
        string='Annual Inspection Due Soon',
        compute='_compute_annual_inspection_due_soon',
        help="True if annual inspection is due within warning period.",
    )
    
    # === Insurance & Certificates ===
    insurance_policy = fields.Char(
        string='Insurance Policy #',
    )
    insurance_expiry = fields.Date(
        string='Insurance Expiry',
        tracking=True,
    )
    cof_a_expiry = fields.Date(
        string='C of A Expiry',
        tracking=True,
        help="Certificate of Airworthiness expiry date.",
    )
    arc_expiry = fields.Date(
        string='ARC Expiry',
        tracking=True,
        help="Airworthiness Review Certificate expiry date.",
    )
    
    # === Location ===
    home_base = fields.Char(
        string='Home Base',
        help="ICAO code of home airport (e.g., DTTI).",
    )
    
    # === Images ===
    image = fields.Image(
        string='Photo',
        max_width=1920,
        max_height=1080,
    )
    image_128 = fields.Image(
        string='Thumbnail',
        related='image',
        max_width=128,
        max_height=128,
        store=True,
    )
    
    # === Administrative ===
    notes = fields.Text(
        string='Notes',
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )

    _registration_unique = models.Constraint(
        'UNIQUE(registration)',
        'Aircraft registration must be unique!',
    )

    @api.depends('registration', 'aircraft_type_id.full_name')
    def _compute_display_name(self):
        for record in self:
            type_name = record.aircraft_type_id.full_name if record.aircraft_type_id else ''  # type: ignore[attr-defined]
            record.display_name = f"{record.registration} ({type_name})"

    @api.depends('status')
    def _compute_status_color(self):
        color_map = {
            'available': 10,    # Green
            'in_use': 4,        # Blue
            'maintenance': 3,   # Yellow
            'grounded': 1,      # Red
            'reserved': 2,      # Orange
        }
        for record in self:
            record.status_color = color_map.get(record.status or 'available', 0)

    @api.depends('status')
    def _compute_is_airworthy(self):
        for record in self:
            record.is_airworthy = record.status in ('available', 'in_use', 'reserved')

    @api.depends('maintenance_due_at_hours', 'total_hours')
    def _compute_remaining_maintenance_hours(self):
        for record in self:
            if record.maintenance_due_at_hours:
                record.remaining_maintenance_hours = record.maintenance_due_at_hours - record.total_hours
            else:
                record.remaining_maintenance_hours = 0.0

    @api.depends('next_maintenance_date', 'remaining_maintenance_hours')
    def _compute_maintenance_status(self):
        today = date.today()
        config_param = self.env['ir.config_parameter'].sudo()
        warning_hours = float(config_param.get_param('flight_school.maintenance_warning_hours', '10.0'))
        
        for record in self:
            status = 'ok'
            
            # Check date-based maintenance
            if record.next_maintenance_date:
                days_until = (record.next_maintenance_date - today).days
                if days_until < 0:
                    status = 'overdue'
                elif days_until <= 7:
                    status = 'due_soon'
            
            # Check hours-based maintenance
            if record.remaining_maintenance_hours:
                if record.remaining_maintenance_hours < 0:
                    status = 'overdue'
                elif record.remaining_maintenance_hours <= warning_hours and status != 'overdue':
                    status = 'due_soon'
            
            record.maintenance_status = status

    @api.depends('annual_inspection_date')
    def _compute_annual_inspection_due_soon(self):
        today = date.today()
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.annual_inspection_warning_days', '30'
        ))
        for record in self:
            if record.annual_inspection_date:
                days_until = (record.annual_inspection_date - today).days
                record.annual_inspection_due_soon = days_until <= warning_days
            else:
                record.annual_inspection_due_soon = False

    @api.onchange('registration')
    def _onchange_registration_uppercase(self):
        if self.registration:
            self.registration = self.registration.upper()

    @api.constrains('registration')
    def _check_registration_format(self):
        for record in self:
            if record.registration and not record.registration.replace('-', '').isalnum():
                raise UserError("Registration must contain only letters, numbers, and hyphens.")

    def action_set_available(self):
        """Set aircraft status to available."""
        self.write({'status': 'available', 'status_reason': False})

    def action_set_maintenance(self):
        """Set aircraft status to in maintenance."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Set Maintenance Status',
            'res_model': 'fs.aircraft',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_status': 'maintenance'},
        }

    def action_set_grounded(self):
        """Set aircraft status to grounded."""
        self.write({'status': 'grounded'})

    def unlink(self):
        for record in self:
            if record.total_hours > 0:
                raise UserError(
                    f"Cannot delete aircraft '{record.registration}' with flight history. "
                    "Archive it instead by unchecking 'Active'."
                )
        return super().unlink()
